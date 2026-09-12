"""Macro definitions and the cooperative macro engine.

A macro is a list of step strings.  Each step is one of::

    <combo>                 tap the key combination, e.g. "ctrl+alt+delete"
    tap <combo>             same as a bare combo
    press <combo>           press and hold
    release <combo>         release specific keys
    release all             release every key and mouse button held by macros
    type <text>             type text using the US layout (rest of the line)
    wait <ms>               pause
    mouse move <dx> <dy>    relative motion
    mouse to <x> <y>        absolute position 0..32767 (absolute mouse mode)
    mouse click <button> [n]  click n times (left/right/middle/back/forward)
    mouse down <button>
    mouse up <button>
    mouse wheel <n>         positive = away from the user
    macro <name>            run another macro inline (max depth 8)

Steps execute cooperatively from the bridge's main loop: each step yields a
delay and pass-through input keeps flowing while a macro is waiting.
"""
from __future__ import annotations

import heapq
import itertools
import logging
import shlex
import time
from dataclasses import dataclass, field
from typing import Callable, Generator, Iterable, Protocol

from .keymap import US_LAYOUT, usage_from_name
from .reports import BUTTON_NAMES

log = logging.getLogger("hid-bridge.macros")

MAX_DEPTH = 8


class MacroError(Exception):
    pass


@dataclass
class Step:
    kind: str
    keys: tuple[int, ...] = ()
    text: str = ""
    ms: int = 0
    dx: int = 0
    dy: int = 0
    button: int = 0
    count: int = 1
    name: str = ""

    def describe(self) -> str:
        if self.kind == "type":
            return f"type {self.text!r}"
        if self.kind in ("tap", "press", "release"):
            return f"{self.kind} {'+'.join(f'0x{u:02x}' for u in self.keys)}"
        if self.kind == "wait":
            return f"wait {self.ms}"
        if self.kind == "macro":
            return f"macro {self.name}"
        return self.kind


def parse_combo(text: str) -> tuple[int, ...]:
    parts = [p for p in text.strip().split("+") if p != ""]
    if text.strip().endswith("+") and text.strip() != "+":
        # "ctrl++" means ctrl plus the '+' key
        parts.append("plus")
    if text.strip() == "+":
        parts = ["plus"]
    if not parts:
        raise MacroError("empty key combination")
    usages: list[int] = []
    for part in parts:
        try:
            usage = usage_from_name(part)
        except KeyError as exc:
            raise MacroError(str(exc)) from exc
        if usage not in usages:
            usages.append(usage)
    return tuple(usages)


def _int_arg(value: str, what: str) -> int:
    try:
        return int(value, 0)
    except ValueError:
        raise MacroError(f"{what}: expected an integer, got {value!r}")


def _button(value: str) -> int:
    key = value.lower()
    if key not in BUTTON_NAMES:
        raise MacroError(f"unknown mouse button {value!r} (use left/right/middle/back/forward)")
    return BUTTON_NAMES[key]


def parse_step(text: str, known_macros: dict[str, Iterable[str]] | None = None) -> Step:
    raw = text.strip()
    if not raw:
        raise MacroError("empty step")
    head, _, rest = raw.partition(" ")
    verb = head.lower()
    rest = rest.strip()

    if verb == "type":
        body = raw[len(head):]
        if body.startswith(" "):
            body = body[1:]
        return Step("type", text=body)
    if verb == "wait":
        ms = _int_arg(rest, "wait")
        if ms < 0:
            raise MacroError("wait: delay must be >= 0")
        return Step("wait", ms=ms)
    if verb in ("tap", "press"):
        if not rest:
            raise MacroError(f"{verb}: missing key combination")
        return Step(verb, keys=parse_combo(rest))
    if verb == "release":
        if rest.lower() == "all":
            return Step("release_all")
        if not rest:
            raise MacroError("release: missing key combination (or 'all')")
        return Step("release", keys=parse_combo(rest))
    if verb == "macro":
        if not rest:
            raise MacroError("macro: missing name")
        if known_macros is not None and rest not in known_macros:
            raise MacroError(f"macro: no such macro {rest!r}")
        return Step("macro", name=rest)
    if verb == "mouse":
        args = shlex.split(rest)
        if not args:
            raise MacroError("mouse: missing sub-command")
        sub = args[0].lower()
        if sub == "move" and len(args) == 3:
            return Step("mouse_move", dx=_int_arg(args[1], "dx"), dy=_int_arg(args[2], "dy"))
        if sub == "to" and len(args) == 3:
            return Step("mouse_to", dx=_int_arg(args[1], "x"), dy=_int_arg(args[2], "y"))
        if sub == "click" and len(args) in (2, 3):
            count = _int_arg(args[2], "count") if len(args) == 3 else 1
            if count < 1:
                raise MacroError("mouse click: count must be >= 1")
            return Step("mouse_click", button=_button(args[1]), count=count)
        if sub == "down" and len(args) == 2:
            return Step("mouse_down", button=_button(args[1]))
        if sub == "up" and len(args) == 2:
            return Step("mouse_up", button=_button(args[1]))
        if sub == "wheel" and len(args) == 2:
            return Step("mouse_wheel", dy=_int_arg(args[1], "wheel"))
        raise MacroError(f"mouse: bad sub-command {rest!r}")
    # Anything else is a bare key combination.
    return Step("tap", keys=parse_combo(raw))


class MacroTarget(Protocol):
    """What the macro engine needs from the bridge."""

    def macro_keys_changed(self) -> None: ...
    def macro_mouse_move(self, dx: int, dy: int, wheel: int) -> None: ...
    def macro_mouse_to(self, x: int, y: int) -> None: ...
    def macro_buttons_changed(self) -> None: ...


@dataclass(order=True)
class _Scheduled:
    when: float
    seq: int
    task: "MacroTask" = field(compare=False)


class MacroTask:
    def __init__(self, engine: "MacroEngine", label: str, steps: list[Step], depth: int = 0):
        self.engine = engine
        self.label = label
        self.steps = steps
        self.depth = depth
        self.gen = self._run()
        self.done = False

    def _run(self) -> Generator[float, None, None]:
        eng = self.engine
        tap = eng.tap_ms / 1000.0
        gap = eng.step_ms / 1000.0
        for step in self.steps:
            kind = step.kind
            if kind == "tap":
                eng.press(step.keys)
                yield tap
                eng.release(step.keys)
                yield gap
            elif kind == "press":
                eng.press(step.keys)
                yield gap
            elif kind == "release":
                eng.release(step.keys)
                yield gap
            elif kind == "release_all":
                eng.release_all()
                yield gap
            elif kind == "type":
                for ch in step.text:
                    entry = US_LAYOUT.get(ch)
                    if entry is None:
                        log.warning("macro %s: cannot type %r with the US layout, skipped", self.label, ch)
                        continue
                    usage, shift = entry
                    keys = (0xE1, usage) if shift else (usage,)
                    eng.press(keys)
                    yield tap
                    eng.release(keys)
                    yield gap
            elif kind == "wait":
                yield step.ms / 1000.0
            elif kind == "mouse_move":
                eng.target.macro_mouse_move(step.dx, step.dy, 0)
                yield gap
            elif kind == "mouse_to":
                eng.target.macro_mouse_to(step.dx, step.dy)
                yield gap
            elif kind == "mouse_wheel":
                eng.target.macro_mouse_move(0, 0, step.dy)
                yield gap
            elif kind == "mouse_down":
                eng.button(step.button, True)
                yield gap
            elif kind == "mouse_up":
                eng.button(step.button, False)
                yield gap
            elif kind == "mouse_click":
                for _ in range(step.count):
                    eng.button(step.button, True)
                    yield tap
                    eng.button(step.button, False)
                    yield gap
            elif kind == "macro":
                if self.depth >= MAX_DEPTH:
                    raise MacroError(f"macro nesting deeper than {MAX_DEPTH} ({step.name})")
                sub_steps = eng.compile(step.name)
                sub = MacroTask(eng, f"{self.label}>{step.name}", sub_steps, self.depth + 1)
                yield from sub.gen
            else:  # pragma: no cover
                raise MacroError(f"unknown step kind {kind}")


class MacroEngine:
    def __init__(self, target: MacroTarget, macros: dict[str, list[str]], tap_ms: int = 30, step_ms: int = 20):
        self.target = target
        self.macros = macros
        self.tap_ms = tap_ms
        self.step_ms = step_ms
        self.pressed: set[int] = set()
        self.buttons = 0
        self._queue: list[_Scheduled] = []
        self._seq = itertools.count()
        self._compiled: dict[str, list[Step]] = {}
        self.running = 0
        self.completed = 0
        self.failed = 0

    # -- state used by the bridge when merging reports ------------------------
    def press(self, keys: Iterable[int]) -> None:
        self.pressed.update(keys)
        self.target.macro_keys_changed()

    def release(self, keys: Iterable[int]) -> None:
        self.pressed.difference_update(keys)
        self.target.macro_keys_changed()

    def release_all(self) -> None:
        self.pressed.clear()
        self.buttons = 0
        self.target.macro_keys_changed()
        self.target.macro_buttons_changed()

    def button(self, bit: int, down: bool) -> None:
        if down:
            self.buttons |= 1 << bit
        else:
            self.buttons &= ~(1 << bit)
        self.target.macro_buttons_changed()

    # -- scheduling -----------------------------------------------------------
    def compile(self, name: str) -> list[Step]:
        if name not in self.macros:
            raise MacroError(f"no such macro: {name}")
        if name not in self._compiled:
            self._compiled[name] = [parse_step(s, self.macros) for s in self.macros[name]]
        return self._compiled[name]

    def start(self, name: str, now: float | None = None) -> None:
        self.start_steps(self.compile(name), label=name, now=now)

    def start_steps(self, steps: list[Step], label: str = "adhoc", now: float | None = None) -> None:
        task = MacroTask(self, label, steps)
        self.running += 1
        log.info("macro %s started (%d steps)", label, len(steps))
        self._advance(task, time.monotonic() if now is None else now)

    def next_deadline(self) -> float | None:
        return self._queue[0].when if self._queue else None

    def run_due(self, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        while self._queue and self._queue[0].when <= now:
            item = heapq.heappop(self._queue)
            self._advance(item.task, now)

    def _advance(self, task: MacroTask, now: float) -> None:
        try:
            delay = next(task.gen)
        except StopIteration:
            task.done = True
            self.running -= 1
            self.completed += 1
            log.info("macro %s finished", task.label)
            return
        except MacroError as exc:
            task.done = True
            self.running -= 1
            self.failed += 1
            log.error("macro %s aborted: %s", task.label, exc)
            self.release_all()
            return
        heapq.heappush(self._queue, _Scheduled(now + max(0.0, delay), next(self._seq), task))

    def stats(self) -> dict:
        return {
            "running": self.running,
            "completed": self.completed,
            "failed": self.failed,
            "keys_held": sorted(self.pressed),
            "buttons_held": self.buttons,
            "defined": sorted(self.macros),
        }
