"""configfs/libcomposite USB gadget management.

Creates a single-configuration gadget with two HID functions:

* interface 0: boot-protocol keyboard  -> /dev/hidgN (keyboard)
* interface 1: boot-protocol mouse     -> /dev/hidgM (mouse)

Everything the kernel lets user space control is pinned to the values a
plain full-speed keyboard/mouse combo exposes.  See docs/usb-identity.md for
the fields libcomposite fixes itself.
"""
from __future__ import annotations

import errno
import json
import logging
import os
import re
import stat
import subprocess
import time

from .config import Config
from .descriptors import (
    HID_PROTOCOL_KEYBOARD,
    HID_PROTOCOL_MOUSE,
    HID_SUBCLASS_BOOT,
    KEYBOARD_REPORT_LENGTH,
    keyboard_report_descriptor,
    mouse_report_descriptor,
    mouse_report_length,
)

log = logging.getLogger("hid-bridge.gadget")

STATE_DIR = "/run/hid-bridge"
STATE_FILE = os.path.join(STATE_DIR, "gadget.json")
UDC_SYSFS = "/sys/class/udc"

KEYBOARD_FUNCTION = "hid.kbd"
MOUSE_FUNCTION = "hid.mouse"


class GadgetError(Exception):
    pass


def _write(path: str, value: str | bytes) -> None:
    mode = "wb" if isinstance(value, bytes) else "w"
    with open(path, mode) as fh:
        fh.write(value)


def _read(path: str, default: str = "") -> str:
    try:
        with open(path) as fh:
            return fh.read().strip()
    except OSError:
        return default


def _write_optional(path: str, value: str, feature: str, warnings: list[str]) -> bool:
    if not os.path.exists(path):
        warnings.append(f"kernel lacks {feature} ({os.path.basename(path)}); skipped")
        return False
    try:
        _write(path, value)
        return True
    except OSError as exc:
        warnings.append(f"could not set {feature}: {exc.strerror}")
        return False


def list_udcs() -> list[str]:
    try:
        return sorted(os.listdir(UDC_SYSFS))
    except FileNotFoundError:
        return []


def udc_lpm_enabled(udc: str) -> bool | None:
    """Whether dwc2 runs with LPM enabled (decides bcdUSB 2.00 vs 2.01 + BOS).

    Read from debugfs; None when debugfs is unavailable.
    """
    text = _read(f"/sys/kernel/debug/usb/{udc}/params")
    match = re.search(r"^\s*lpm\s*[:=]\s*(\d)", text, re.M)
    return None if not match else match.group(1) == "1"


def udc_current_state(udc: str) -> str:
    """Cheap read of /sys/class/udc/<udc>/state for the bridge's periodic poll."""
    return _read(os.path.join(UDC_SYSFS, udc, "state"), "unknown")


def udc_state(udc: str) -> dict:
    base = os.path.join(UDC_SYSFS, udc)
    lpm = udc_lpm_enabled(udc)
    return {
        "udc": udc,
        "state": _read(os.path.join(base, "state"), "unknown"),
        "current_speed": _read(os.path.join(base, "current_speed"), "unknown"),
        "maximum_speed": _read(os.path.join(base, "maximum_speed"), "unknown"),
        "function": _read(os.path.join(base, "function"), ""),
        "lpm": lpm,
        "bcdUSB_on_wire": "unknown" if lpm is None else ("0x0201 (+BOS)" if lpm else "0x0200"),
    }


def _find_hidg_by_dev(major_minor: str) -> str | None:
    try:
        major_s, minor_s = major_minor.strip().split(":")
        wanted = os.makedev(int(major_s), int(minor_s))
    except ValueError:
        return None
    try:
        names = os.listdir("/dev")
    except OSError:
        return None
    for name in names:
        if not name.startswith("hidg"):
            continue
        path = f"/dev/{name}"
        try:
            st = os.stat(path)
        except OSError:
            continue
        if stat.S_ISCHR(st.st_mode) and st.st_rdev == wanted:
            return path
    return None


class Gadget:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.g = cfg.gadget
        self.path = os.path.join(self.g.configfs, self.g.name)
        self.warnings: list[str] = []

    # -- helpers ---------------------------------------------------------------
    def _p(self, *parts: str) -> str:
        return os.path.join(self.path, *parts)

    def exists(self) -> bool:
        return os.path.isdir(self.path)

    def bound_udc(self) -> str:
        return _read(self._p("UDC")) if self.exists() else ""

    def ensure_configfs(self) -> None:
        if os.path.isdir(self.g.configfs):
            return
        if not os.path.isdir("/sys/kernel/config"):
            subprocess.run(["mount", "-t", "configfs", "none", "/sys/kernel/config"], check=False)
        if not os.path.isdir(self.g.configfs):
            subprocess.run(["modprobe", "libcomposite"], check=False)
        for _ in range(20):
            if os.path.isdir(self.g.configfs):
                return
            time.sleep(0.1)
        raise GadgetError(f"{self.g.configfs} is not available: is libcomposite loaded and configfs mounted?")

    def pick_udc(self, timeout: float = 15.0) -> str:
        deadline = time.monotonic() + timeout
        while True:
            udcs = list_udcs()
            if self.g.udc:
                if self.g.udc in udcs:
                    return self.g.udc
            elif udcs:
                if len(udcs) > 1:
                    self.warnings.append(f"several UDCs present ({', '.join(udcs)}); using {udcs[0]}")
                return udcs[0]
            if time.monotonic() >= deadline:
                break
            time.sleep(0.25)
        wanted = self.g.udc or "any"
        raise GadgetError(
            f"no USB device controller found (wanted: {wanted}). "
            "Add 'dtoverlay=dwc2,dr_mode=peripheral' to /boot/firmware/config.txt, "
            "load the dwc2 module and reboot."
        )

    # -- descriptors -----------------------------------------------------------
    def keyboard_descriptor(self) -> bytes:
        return keyboard_report_descriptor(self.cfg.keyboard.descriptor == "extended")

    def mouse_descriptor(self) -> bytes:
        return mouse_report_descriptor(self.cfg.mouse.mode, self.cfg.mouse.buttons)

    # -- lifecycle -------------------------------------------------------------
    def up(self) -> dict:
        self.warnings = []
        self.ensure_configfs()
        if self.exists():
            if self.bound_udc():
                log.info("gadget %s already bound to %s", self.g.name, self.bound_udc())
                devices = self.resolve_devices()
                self._write_state(devices)
                return devices
            log.info("gadget %s exists but is unbound; rebuilding", self.g.name)
            self.down()

        g = self.g
        os.makedirs(self._p("strings", "0x409"), exist_ok=True)
        os.makedirs(self._p("configs", "c.1"), exist_ok=True)
        os.makedirs(self._p("functions", KEYBOARD_FUNCTION), exist_ok=True)
        os.makedirs(self._p("functions", MOUSE_FUNCTION), exist_ok=True)

        # Device descriptor
        _write(self._p("idVendor"), f"0x{g.vendor_id:04x}")
        _write(self._p("idProduct"), f"0x{g.product_id:04x}")
        _write(self._p("bcdDevice"), f"0x{g.device_version:04x}")
        # libcomposite recomputes bcdUSB (0x0200, or 0x0201 with LPM) and
        # bMaxPacketSize0 (dwc2 EP0 = 64) when answering GET_DESCRIPTOR; write
        # the values it will emit so configfs reflects the wire.
        _write(self._p("bcdUSB"), "0x0200")
        _write(self._p("bDeviceClass"), "0x00")     # class defined per interface
        _write(self._p("bDeviceSubClass"), "0x00")
        _write(self._p("bDeviceProtocol"), "0x00")
        _write(self._p("bMaxPacketSize0"), "0x40")
        _write_optional(self._p("max_speed"), g.max_speed, "max_speed selection", self.warnings)

        # Strings.  Once the language directory exists libcomposite always
        # allocates iManufacturer=1, iProduct=2, iSerialNumber=3 and answers an
        # unset one with an empty string descriptor.  A real keyboard has
        # either a set of real strings or none at all, so either fill all
        # three or leave all three empty (no strings directory).
        if g.manufacturer or g.product or g.serial:
            for attr, value in (("manufacturer", g.manufacturer), ("product", g.product), ("serialnumber", g.serial)):
                if value:
                    _write(self._p("strings", "0x409", attr), value)
                else:
                    self.warnings.append(
                        f"gadget.{attr} is empty: the kernel presents string #{('manufacturer', 'product', 'serialnumber').index(attr) + 1} "
                        "as an empty descriptor; set it or clear all three strings")
        else:
            os.rmdir(self._p("strings", "0x409"))

        # Configuration descriptor: bus powered (bit 7 always set), optional
        # self-powered (bit 6) and remote-wakeup (bit 5) bits.
        attrs = 0x80 | (0x40 if g.self_powered else 0) | (0x20 if g.remote_wakeup else 0)
        _write(self._p("configs", "c.1", "bmAttributes"), f"0x{attrs:02x}")
        _write(self._p("configs", "c.1", "MaxPower"), str(g.max_power_ma))

        # Keyboard function
        kbd = self._p("functions", KEYBOARD_FUNCTION)
        _write(os.path.join(kbd, "protocol"), str(HID_PROTOCOL_KEYBOARD))
        _write(os.path.join(kbd, "subclass"), str(HID_SUBCLASS_BOOT))
        _write(os.path.join(kbd, "report_length"), str(KEYBOARD_REPORT_LENGTH))
        _write(os.path.join(kbd, "report_desc"), self.keyboard_descriptor())
        _write_optional(os.path.join(kbd, "no_out_endpoint"), "1", "single-IN-endpoint HID (no_out_endpoint)", self.warnings)
        if g.remote_wakeup:
            _write_optional(os.path.join(kbd, "wakeup_on_write"), "1", "remote wakeup on keypress (wakeup_on_write)", self.warnings)
        _write_optional(os.path.join(kbd, "interval"), str(self.cfg.keyboard.poll_interval_ms), "keyboard bInterval", self.warnings)

        # Mouse function
        mouse = self._p("functions", MOUSE_FUNCTION)
        if self.cfg.mouse.mode == "relative":
            _write(os.path.join(mouse, "protocol"), str(HID_PROTOCOL_MOUSE))
            _write(os.path.join(mouse, "subclass"), str(HID_SUBCLASS_BOOT))
        else:
            # An absolute pointer is not a boot-protocol mouse; say so honestly.
            _write(os.path.join(mouse, "protocol"), "0")
            _write(os.path.join(mouse, "subclass"), "0")
        _write(os.path.join(mouse, "report_length"), str(mouse_report_length(self.cfg.mouse.mode)))
        _write(os.path.join(mouse, "report_desc"), self.mouse_descriptor())
        _write_optional(os.path.join(mouse, "no_out_endpoint"), "1", "single-IN-endpoint HID (no_out_endpoint)", self.warnings)
        _write_optional(os.path.join(mouse, "interval"), str(self.cfg.mouse.poll_interval_ms), "mouse bInterval", self.warnings)

        # Interface order = link order: keyboard first, mouse second.
        os.symlink(kbd, self._p("configs", "c.1", KEYBOARD_FUNCTION))
        os.symlink(mouse, self._p("configs", "c.1", MOUSE_FUNCTION))

        udc = self.pick_udc()
        try:
            _write(self._p("UDC"), udc)
        except OSError as exc:
            if exc.errno == errno.EBUSY:
                raise GadgetError(f"UDC {udc} is busy: another gadget is bound to it (check {self.g.configfs})") from exc
            raise
        log.info("gadget %s bound to %s", g.name, udc)

        devices = self.resolve_devices()
        self._write_state(devices)
        for warning in self.warnings:
            log.warning("%s", warning)
        return devices

    def down(self) -> None:
        if not self.exists():
            return
        try:
            if self.bound_udc():
                _write(self._p("UDC"), "")
        except OSError as exc:
            log.warning("unbinding UDC failed: %s", exc)
        for func in (KEYBOARD_FUNCTION, MOUSE_FUNCTION):
            link = self._p("configs", "c.1", func)
            if os.path.islink(link):
                os.unlink(link)
        for directory in (
            self._p("configs", "c.1", "strings", "0x409"),
            self._p("configs", "c.1"),
            self._p("functions", KEYBOARD_FUNCTION),
            self._p("functions", MOUSE_FUNCTION),
            self._p("strings", "0x409"),
            self.path,
        ):
            if os.path.isdir(directory):
                try:
                    os.rmdir(directory)
                except OSError as exc:
                    log.warning("rmdir %s: %s", directory, exc.strerror)
        try:
            os.unlink(STATE_FILE)
        except OSError:
            pass
        log.info("gadget %s removed", self.g.name)

    # -- device resolution ------------------------------------------------------
    def resolve_devices(self, timeout: float = 5.0) -> dict:
        """Map the two functions to their /dev/hidgN nodes."""
        result: dict[str, str] = {}
        deadline = time.monotonic() + timeout
        while True:
            for role, func in (("keyboard", KEYBOARD_FUNCTION), ("mouse", MOUSE_FUNCTION)):
                if role in result:
                    continue
                dev_attr = _read(self._p("functions", func, "dev"))
                path = _find_hidg_by_dev(dev_attr) if dev_attr else None
                if path:
                    result[role] = path
            if len(result) == 2 or time.monotonic() >= deadline:
                break
            time.sleep(0.1)
        if len(result) < 2:
            # Old kernels without the 'dev' attribute: fall back to creation order.
            fallback = {"keyboard": "/dev/hidg0", "mouse": "/dev/hidg1"}
            for role, path in fallback.items():
                if role not in result and os.path.exists(path):
                    result[role] = path
                    self.warnings.append(f"assumed {path} is the {role} (kernel has no hid 'dev' attribute)")
        if len(result) < 2:
            raise GadgetError("could not find /dev/hidg* devices for the gadget functions")
        return {
            "gadget": self.path,
            "udc": self.bound_udc(),
            "keyboard": result["keyboard"],
            "mouse": result["mouse"],
            "keyboard_report_length": KEYBOARD_REPORT_LENGTH,
            "mouse_report_length": mouse_report_length(self.cfg.mouse.mode),
        }

    def _write_state(self, devices: dict) -> None:
        try:
            os.makedirs(STATE_DIR, exist_ok=True)
            with open(STATE_FILE, "w") as fh:
                json.dump(devices, fh, indent=2)
        except OSError as exc:
            log.warning("cannot write %s: %s", STATE_FILE, exc)

    def status(self) -> dict:
        info: dict = {"gadget": self.path, "exists": self.exists(), "bound": False}
        if not self.exists():
            info["udcs"] = list_udcs()
            return info
        udc = self.bound_udc()
        info["bound"] = bool(udc)
        info["descriptor"] = {
            "idVendor": _read(self._p("idVendor")),
            "idProduct": _read(self._p("idProduct")),
            "bcdDevice": _read(self._p("bcdDevice")),
            "bcdUSB": _read(self._p("bcdUSB")),
            "max_speed": _read(self._p("max_speed"), "n/a"),
            "manufacturer": _read(self._p("strings", "0x409", "manufacturer")),
            "product": _read(self._p("strings", "0x409", "product")),
            "serialnumber": _read(self._p("strings", "0x409", "serialnumber")),
            "bmAttributes": _read(self._p("configs", "c.1", "bmAttributes")),
            "MaxPower": _read(self._p("configs", "c.1", "MaxPower")),
        }
        info["functions"] = {}
        for role, func in (("keyboard", KEYBOARD_FUNCTION), ("mouse", MOUSE_FUNCTION)):
            base = self._p("functions", func)
            if os.path.isdir(base):
                info["functions"][role] = {
                    "protocol": _read(os.path.join(base, "protocol")),
                    "subclass": _read(os.path.join(base, "subclass")),
                    "report_length": _read(os.path.join(base, "report_length")),
                    "no_out_endpoint": _read(os.path.join(base, "no_out_endpoint"), "n/a"),
                    "wakeup_on_write": _read(os.path.join(base, "wakeup_on_write"), "n/a"),
                    "interval": _read(os.path.join(base, "interval"), "n/a"),
                    "dev": _read(os.path.join(base, "dev"), "n/a"),
                }
        if udc:
            info["udc"] = udc_state(udc)
            try:
                info["devices"] = self.resolve_devices(timeout=0.5)
            except GadgetError as exc:
                info["devices_error"] = str(exc)
        return info


def load_state() -> dict | None:
    try:
        with open(STATE_FILE) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None
