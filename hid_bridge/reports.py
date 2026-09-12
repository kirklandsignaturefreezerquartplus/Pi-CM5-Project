"""HID input report construction."""
from __future__ import annotations

import struct
from typing import Iterable, Iterator

from . import linux_input as li
from .descriptors import ABS_MAX_VALUE
from .keymap import BOOT_DESCRIPTOR_MAX_USAGE, is_modifier

KEYBOARD_IDLE_REPORT = bytes(8)
ERROR_ROLLOVER = 0x01


def keyboard_report(usages: Iterable[int], max_array_usage: int = 0xFF) -> bytes:
    """Build the 8-byte boot keyboard report for the set of pressed usages.

    Usages outside 0x04..max_array_usage are silently dropped (they are not
    representable with the active descriptor).  More than six simultaneous
    non-modifier keys produce the ErrorRollOver phantom state as the HID
    specification requires (all six slots set to 0x01).
    """
    modifiers = 0
    keys: list[int] = []
    for usage in sorted(set(usages)):
        if is_modifier(usage):
            modifiers |= 1 << (usage - 0xE0)
        elif 0x04 <= usage <= max_array_usage:
            keys.append(usage)
    if len(keys) > 6:
        keys = [ERROR_ROLLOVER] * 6
    keys += [0] * (6 - len(keys))
    return bytes([modifiers, 0x00] + keys)


def keyboard_max_array_usage(descriptor_kind: str) -> int:
    return BOOT_DESCRIPTOR_MAX_USAGE if descriptor_kind == "boot" else 0xFF


BUTTON_BITS: dict[int, int] = {
    li.BTN_LEFT: 0,
    li.BTN_RIGHT: 1,
    li.BTN_MIDDLE: 2,
    li.BTN_SIDE: 3,
    li.BTN_BACK: 3,
    li.BTN_EXTRA: 4,
    li.BTN_FORWARD: 4,
}

BUTTON_NAMES: dict[str, int] = {
    "left": 0, "right": 1, "middle": 2, "back": 3, "side": 3, "forward": 4, "extra": 4,
    "1": 0, "2": 1, "3": 2, "4": 3, "5": 4,
}


def clamp(value: int, low: int, high: int) -> int:
    return low if value < low else high if value > high else value


def split_delta(value: int, limit: int = 127) -> Iterator[int]:
    """Yield chunks of ``value`` each within [-limit, limit]."""
    while value > limit:
        yield limit
        value -= limit
    while value < -limit:
        yield -limit
        value += limit
    yield value


def relative_mouse_reports(buttons: int, dx: int, dy: int, wheel: int, button_count: int) -> list[bytes]:
    """Return one or more 4-byte relative mouse reports encoding the motion.

    Motion larger than +-127 is split across several reports so nothing is
    lost, mirroring what a real mouse does at high speed.
    """
    mask = (1 << button_count) - 1
    buttons &= mask
    xs = list(split_delta(dx))
    ys = list(split_delta(dy))
    ws = list(split_delta(wheel))
    count = max(len(xs), len(ys), len(ws))
    xs += [0] * (count - len(xs))
    ys += [0] * (count - len(ys))
    ws += [0] * (count - len(ws))
    return [struct.pack("<Bbbb", buttons, x, y, w) for x, y, w in zip(xs, ys, ws)]


def absolute_mouse_report(buttons: int, x: int, y: int, wheel: int, button_count: int) -> bytes:
    mask = (1 << button_count) - 1
    return struct.pack(
        "<BHHb",
        buttons & mask,
        clamp(x, 0, ABS_MAX_VALUE),
        clamp(y, 0, ABS_MAX_VALUE),
        clamp(wheel, -127, 127),
    )


def scale_abs(value: int, minimum: int, span: int, out_max: int = ABS_MAX_VALUE) -> int:
    """Scale an evdev absolute value from [minimum, minimum+span] to [0, out_max]."""
    if span <= 0:
        return 0
    return clamp(round((value - minimum) * out_max / span), 0, out_max)


LED_BIT_TO_EVDEV: dict[int, int] = {
    0: li.LED_NUML,
    1: li.LED_CAPSL,
    2: li.LED_SCROLLL,
    3: li.LED_COMPOSE,
    4: li.LED_KANA,
}
