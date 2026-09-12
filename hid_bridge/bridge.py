"""The bridge daemon: evdev sources in, HID gadget reports out."""
from __future__ import annotations

import logging
import os
import select
import signal
import time

from . import linux_input as li
from .config import Config, InputRule
from .control import ControlServer
from .descriptors import ABS_MAX_VALUE, KEYBOARD_REPORT_LENGTH, mouse_report_length
from .gadget import udc_current_state, udc_state
from .hidg import HidgDevice
from .keymap import CODE_NAMES, EVDEV_TO_HID, KEY_CODES
from .linux_input import InputDevice, list_event_nodes
from .macros import MacroEngine, MacroError, Step, parse_step
from .reports import (
    BUTTON_BITS,
    LED_BIT_TO_EVDEV,
    absolute_mouse_report,
    clamp,
    keyboard_max_array_usage,
    keyboard_report,
    relative_mouse_reports,
    scale_abs,
)

log = logging.getLogger("hid-bridge")


class Source:
    """One attached evdev device and the state it contributes."""

    def __init__(self, dev: InputDevice, rule: InputRule):
        self.dev = dev
        self.rule = rule
        self.role = rule.role
        self.pressed: set[int] = set()
        self.buttons = 0
        self.dx = 0
        self.dy = 0
        self.wheel = 0
        self.abs_x: int | None = None
        self.abs_y: int | None = None
        self.last_px: int | None = None
        self.last_py: int | None = None
        self.mouse_dirty = False
        self.abs_dirty = False
        self.events = 0
        self.attached_at = time.monotonic()
        self.bindings: dict[int, str] = {}
        for key_name, macro_name in rule.bindings.items():
            code = KEY_CODES.get(key_name)
            if code is None:
                log.warning("%s: binding for unknown key %s ignored", dev.name, key_name)
                continue
            self.bindings[code] = macro_name

    def describe(self) -> dict:
        ident = self.dev.identity
        return {
            "path": self.dev.path,
            "name": ident.name,
            "phys": ident.phys,
            "vendor": f"{ident.vendor:04x}",
            "product": f"{ident.product:04x}",
            "keyboard": self.dev.is_keyboard,
            "mouse": self.dev.is_mouse,
            "absolute": self.dev.has_abs_pointer,
            "role": self.role,
            "rule": self.rule.describe(),
            "grabbed": self.dev.grabbed,
            "events": self.events,
            "keys_held": sorted(self.pressed),
            "buttons_held": self.buttons,
        }


class Bridge:
    def __init__(self, cfg: Config, devices: dict):
        self.cfg = cfg
        b = cfg.bridge
        timeout = b.write_timeout_ms / 1000.0
        self.kbd = HidgDevice(devices["keyboard"], KEYBOARD_REPORT_LENGTH, "keyboard", timeout)
        self.mouse = HidgDevice(devices["mouse"], mouse_report_length(cfg.mouse.mode), "mouse", timeout)
        self.udc = devices.get("udc", "")
        self.sources: dict[int, Source] = {}
        self.by_path: dict[str, Source] = {}
        self.ignored: dict[str, str] = {}
        self.retry_after: dict[str, float] = {}
        self.macro = MacroEngine(self, cfg.macros, b.tap_ms, b.step_ms)
        self.max_usage = keyboard_max_array_usage(cfg.keyboard.descriptor)
        self.abs_pos = [ABS_MAX_VALUE // 2, ABS_MAX_VALUE // 2]
        self.leds = 0
        self.control = ControlServer(b.control_socket, self.handle_control) if b.control_socket else None
        self.stop = False
        self.started = time.monotonic()
        self._wake_r, self._wake_w = os.pipe()
        os.set_blocking(self._wake_r, False)
        os.set_blocking(self._wake_w, False)

    # ------------------------------------------------------------------ state
    def all_usages(self) -> set[int]:
        usages = set(self.macro.pressed)
        for src in self.sources.values():
            usages |= src.pressed
        return usages

    def all_buttons(self) -> int:
        buttons = self.macro.buttons
        for src in self.sources.values():
            buttons |= src.buttons
        return buttons

    def _flush_keyboard(self) -> None:
        self.kbd.write_report(keyboard_report(self.all_usages(), self.max_usage))

    def _emit_mouse_motion(self, dx: int, dy: int, wheel: int) -> None:
        buttons = self.all_buttons()
        n = self.cfg.mouse.buttons
        if self.cfg.mouse.mode == "relative":
            # GET_REPORT on a relative mouse answers buttons with zero motion.
            still = relative_mouse_reports(buttons, 0, 0, 0, n)[0]
            for report in relative_mouse_reports(buttons, dx, dy, wheel, n):
                self.mouse.write_report(report, force=True, get_report=still)
            return
        gain = self.cfg.mouse.rel_to_abs_gain
        if dx or dy:
            self.abs_pos[0] = clamp(self.abs_pos[0] + round(dx * gain), 0, ABS_MAX_VALUE)
            self.abs_pos[1] = clamp(self.abs_pos[1] + round(dy * gain), 0, ABS_MAX_VALUE)
        report = absolute_mouse_report(buttons, self.abs_pos[0], self.abs_pos[1], wheel, n)
        still = absolute_mouse_report(buttons, self.abs_pos[0], self.abs_pos[1], 0, n)
        self.mouse.write_report(report, force=bool(wheel), get_report=still)

    def _emit_mouse_absolute(self, x: int | None, y: int | None, wheel: int) -> None:
        if x is not None:
            self.abs_pos[0] = x
        if y is not None:
            self.abs_pos[1] = y
        n = self.cfg.mouse.buttons
        report = absolute_mouse_report(self.all_buttons(), self.abs_pos[0], self.abs_pos[1], wheel, n)
        still = absolute_mouse_report(self.all_buttons(), self.abs_pos[0], self.abs_pos[1], 0, n)
        self.mouse.write_report(report, force=bool(wheel), get_report=still)

    # ----------------------------------------------------------- MacroTarget
    def macro_keys_changed(self) -> None:
        self._flush_keyboard()

    def macro_mouse_move(self, dx: int, dy: int, wheel: int) -> None:
        self._emit_mouse_motion(dx, dy, wheel)

    def macro_mouse_to(self, x: int, y: int) -> None:
        if self.cfg.mouse.mode != "absolute":
            log.warning("'mouse to' needs mouse.mode = \"absolute\"; step ignored")
            return
        self._emit_mouse_absolute(clamp(x, 0, ABS_MAX_VALUE), clamp(y, 0, ABS_MAX_VALUE), 0)

    def macro_buttons_changed(self) -> None:
        self._emit_mouse_motion(0, 0, 0)

    # --------------------------------------------------------------- sources
    def _rescan(self) -> None:
        now = time.monotonic()
        present = set(list_event_nodes())
        for path in list(self.ignored):
            if path not in present:
                del self.ignored[path]
        for path in list(self.retry_after):
            if path not in present:
                del self.retry_after[path]
        for path in sorted(present):
            if path in self.by_path or path in self.ignored:
                continue
            if self.retry_after.get(path, 0) > now:
                continue
            try:
                dev = InputDevice(path)
            except OSError as exc:
                self.retry_after[path] = now + 5.0
                log.debug("%s: cannot open (%s); will retry", path, exc.strerror)
                continue
            ident = dev.identity
            rule = self.cfg.rule_for(ident.name, ident.phys, ident.vendor, ident.product)
            if rule.role == "ignore":
                self.ignored[path] = f"rule {rule.describe()}"
                log.info("%s (%s) ignored by rule %s", path, ident.name, rule.describe())
                dev.close()
                continue
            if not (dev.is_keyboard or dev.is_mouse):
                self.ignored[path] = "not a keyboard or mouse"
                log.debug("%s (%s) is neither keyboard nor mouse; ignored", path, ident.name)
                dev.close()
                continue
            grab = self.cfg.bridge.grab_inputs if rule.grab is None else rule.grab
            if grab:
                try:
                    dev.grab()
                except OSError as exc:
                    log.warning("%s (%s): cannot grab: %s", path, ident.name, exc.strerror)
            src = Source(dev, rule)
            self.sources[dev.fd] = src
            self.by_path[path] = src
            self._apply_leds(src)
            log.info(
                "attached %s: %r [%04x:%04x] kbd=%s mouse=%s abs=%s role=%s (%s)%s",
                path, ident.name, ident.vendor, ident.product, dev.is_keyboard, dev.is_mouse,
                dev.has_abs_pointer, src.role, rule.describe(), " grabbed" if dev.grabbed else "",
            )

    def _remove_source(self, src: Source, reason: str) -> None:
        log.info("detached %s (%r): %s", src.dev.path, src.dev.name, reason)
        self.sources.pop(src.dev.fd, None)
        self.by_path.pop(src.dev.path, None)
        had_keys = bool(src.pressed)
        had_buttons = bool(src.buttons)
        src.pressed.clear()
        src.buttons = 0
        src.dev.close()
        if had_keys:
            self._flush_keyboard()
        if had_buttons:
            self._emit_mouse_motion(0, 0, 0)

    def _apply_leds(self, src: Source) -> None:
        if not self.cfg.bridge.forward_leds or not src.dev.is_keyboard:
            return
        for bit, led in LED_BIT_TO_EVDEV.items():
            src.dev.set_led(led, bool(self.leds & (1 << bit)))

    def _handle_leds(self) -> None:
        data = self.kbd.read_output_report()
        if not data:
            return
        leds = data[0]
        if leds == self.leds:
            return
        self.leds = leds
        log.debug("LED state from host: 0x%02x", leds)
        for src in self.sources.values():
            self._apply_leds(src)

    # ---------------------------------------------------------------- events
    def _process(self, src: Source) -> None:
        try:
            events = src.dev.read_events()
        except OSError as exc:
            self._remove_source(src, exc.strerror or "read error")
            return
        kbd_changed = False
        drop_unbound = src.role == "macro" and src.rule.unbound == "drop"
        for ev_type, code, value in events:
            src.events += 1
            if ev_type == li.EV_KEY:
                if value == 2:
                    continue  # autorepeat: the host generates its own
                if src.role == "macro" and code in src.bindings:
                    if value == 1:
                        name = src.bindings[code]
                        try:
                            self.macro.start(name)
                        except MacroError as exc:
                            log.error("binding %s -> %s: %s", CODE_NAMES.get(code, code), name, exc)
                    continue
                if drop_unbound:
                    continue
                if code >= li.BTN_MOUSE:
                    bit = BUTTON_BITS.get(code)
                    if bit is None:
                        continue
                    if value:
                        src.buttons |= 1 << bit
                    else:
                        src.buttons &= ~(1 << bit)
                    src.mouse_dirty = True
                else:
                    usage = EVDEV_TO_HID.get(code)
                    if usage is None:
                        log.debug("%s: no HID usage for %s", src.dev.name, CODE_NAMES.get(code, code))
                        continue
                    if value:
                        src.pressed.add(usage)
                    else:
                        src.pressed.discard(usage)
                    kbd_changed = True
            elif ev_type == li.EV_REL:
                if drop_unbound:
                    continue
                if code == li.REL_X:
                    src.dx += value
                elif code == li.REL_Y:
                    src.dy += value
                elif code == li.REL_WHEEL:
                    src.wheel += value
                else:
                    continue  # HWHEEL and hi-res variants are not in the descriptor
                src.mouse_dirty = True
            elif ev_type == li.EV_ABS:
                if drop_unbound:
                    continue
                if code == li.ABS_X:
                    src.abs_x = value
                elif code == li.ABS_Y:
                    src.abs_y = value
                else:
                    continue
                src.abs_dirty = True
            elif ev_type == li.EV_SYN and code == li.SYN_REPORT:
                if kbd_changed:
                    self._flush_keyboard()
                    kbd_changed = False
                if src.mouse_dirty or src.abs_dirty:
                    self._flush_source_mouse(src)
        if kbd_changed:
            self._flush_keyboard()

    def _flush_source_mouse(self, src: Source) -> None:
        dx, dy, wheel = src.dx, src.dy, src.wheel
        src.dx = src.dy = src.wheel = 0
        src.mouse_dirty = False
        if src.abs_dirty and src.dev.has_abs_pointer:
            src.abs_dirty = False
            ax = src.dev.absinfo[li.ABS_X]
            ay = src.dev.absinfo[li.ABS_Y]
            if self.cfg.mouse.mode == "absolute":
                x = scale_abs(src.abs_x, ax.minimum, ax.span) if src.abs_x is not None else None
                y = scale_abs(src.abs_y, ay.minimum, ay.span) if src.abs_y is not None else None
                self._emit_mouse_absolute(x, y, wheel)
                return
            # Absolute source, relative output: convert to deltas on a virtual screen.
            width, height = self.cfg.mouse.abs_to_rel_resolution
            if src.abs_x is not None and src.abs_y is not None:
                px = scale_abs(src.abs_x, ax.minimum, ax.span, width - 1)
                py = scale_abs(src.abs_y, ay.minimum, ay.span, height - 1)
                if src.last_px is not None and src.last_py is not None:
                    dx += px - src.last_px
                    dy += py - src.last_py
                src.last_px, src.last_py = px, py
        src.abs_dirty = False
        self._emit_mouse_motion(dx, dy, wheel)

    # --------------------------------------------------------------- control
    def handle_control(self, request: dict) -> dict:
        cmd = request.get("cmd")
        if cmd == "status":
            return self.status()
        if cmd == "inputs":
            return {"sources": [s.describe() for s in self.sources.values()],
                    "ignored": dict(self.ignored)}
        if cmd == "macro":
            name = str(request.get("name", ""))
            self.macro.start(name)
            return {"started": name}
        if cmd == "steps":
            raw = request.get("steps")
            if not isinstance(raw, list) or not raw:
                raise ValueError("'steps' must be a non-empty list of step strings")
            steps = [parse_step(str(s), self.cfg.macros) for s in raw]
            self.macro.start_steps(steps, label="ctl")
            return {"started": [s.describe() for s in steps]}
        if cmd == "type":
            text = str(request.get("text", ""))
            self.macro.start_steps([Step("type", text=text)], label="ctl-type")
            return {"typing": len(text)}
        if cmd == "keys":
            step = parse_step(str(request.get("combo", "")), self.cfg.macros)
            self.macro.start_steps([step], label="ctl-keys")
            return {"started": step.describe()}
        if cmd == "release_all":
            self.macro.release_all()
            for src in self.sources.values():
                src.pressed.clear()
                src.buttons = 0
            self._flush_keyboard()
            self._emit_mouse_motion(0, 0, 0)
            return {"released": True}
        raise ValueError(f"unknown command {cmd!r}")

    def _poll_host_state(self) -> None:
        if not self.udc:
            return
        state = udc_current_state(self.udc)
        self.kbd.host_state_changed(state)
        self.mouse.host_state_changed(state)

    def status(self) -> dict:
        return {
            "uptime_s": round(time.monotonic() - self.started, 1),
            "udc": udc_state(self.udc) if self.udc else {},
            "keyboard": self.kbd.stats(),
            "mouse": {**self.mouse.stats(), "mode": self.cfg.mouse.mode, "buttons": self.cfg.mouse.buttons},
            "leds": self.leds,
            "keys_held": sorted(self.all_usages()),
            "buttons_held": self.all_buttons(),
            "sources": [s.describe() for s in self.sources.values()],
            "macros": self.macro.stats(),
        }

    # ------------------------------------------------------------------ loop
    def _on_signal(self, signum, _frame) -> None:
        self.stop = True
        try:
            os.write(self._wake_w, b"x")
        except OSError:
            pass

    def run(self) -> None:
        signal.signal(signal.SIGTERM, self._on_signal)
        signal.signal(signal.SIGINT, self._on_signal)
        signal.signal(signal.SIGHUP, self._on_signal)
        self.kbd.open()
        self.mouse.open()
        if self.control is not None:
            try:
                self.control.open()
            except OSError as exc:
                log.warning("control socket unavailable: %s", exc)
                self.control = None
        # Start from a clean slate on the host side.
        self.kbd.write_report(bytes(KEYBOARD_REPORT_LENGTH))
        log.info("bridge running: keyboard=%s mouse=%s (%s, %d buttons), sources rescanned every %d ms",
                 self.kbd.path, self.mouse.path, self.cfg.mouse.mode, self.cfg.mouse.buttons,
                 self.cfg.bridge.rescan_interval_ms)
        rescan_every = self.cfg.bridge.rescan_interval_ms / 1000.0
        next_rescan = 0.0
        try:
            while not self.stop:
                now = time.monotonic()
                if now >= next_rescan:
                    self._rescan()
                    self._poll_host_state()
                    next_rescan = now + rescan_every
                self.macro.run_due(now)
                timeout = next_rescan - now
                deadline = self.macro.next_deadline()
                if deadline is not None:
                    timeout = min(timeout, deadline - now)
                timeout = max(0.0, timeout)
                rlist = list(self.sources) + [self._wake_r]
                if self.kbd.poll_readable:
                    rlist.append(self.kbd.fd)
                if self.control is not None:
                    rlist.append(self.control.fileno())
                try:
                    readable, _, _ = select.select(rlist, [], [], timeout)
                except InterruptedError:
                    continue
                except OSError as exc:
                    # A source vanished between rescan and select: drop dead fds.
                    log.debug("select: %s; pruning sources", exc.strerror)
                    for fd, src in list(self.sources.items()):
                        try:
                            os.fstat(fd)
                        except OSError:
                            self._remove_source(src, "fd closed")
                    continue
                for fd in readable:
                    if fd == self._wake_r:
                        try:
                            os.read(self._wake_r, 64)
                        except OSError:
                            pass
                    elif fd == self.kbd.fd:
                        self._handle_leds()
                    elif self.control is not None and fd == self.control.fileno():
                        self.control.handle_ready()
                    elif fd in self.sources:
                        self._process(self.sources[fd])
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        log.info("shutting down: releasing all keys and buttons")
        self.macro.pressed.clear()
        self.macro.buttons = 0
        for src in list(self.sources.values()):
            src.pressed.clear()
            src.buttons = 0
        try:
            self.kbd.write_report(bytes(KEYBOARD_REPORT_LENGTH), force=True)
            self._emit_mouse_motion(0, 0, 0)
        except Exception as exc:  # noqa: BLE001
            log.debug("final reports not delivered: %s", exc)
        for src in list(self.sources.values()):
            src.dev.close()
        self.sources.clear()
        self.by_path.clear()
        if self.control is not None:
            self.control.close()
        self.kbd.close()
        self.mouse.close()
