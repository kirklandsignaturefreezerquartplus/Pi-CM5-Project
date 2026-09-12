"""Minimal pure-Python evdev (Linux input subsystem) access.

Only the standard library is used so the bridge has no third-party
dependencies and can be installed on a stock Raspberry Pi OS Lite image
without pip or network access.
"""
from __future__ import annotations

import array
import fcntl
import os
import struct
from dataclasses import dataclass, field
from typing import Iterable

# ----------------------------------------------------------------------------
# Constants from <linux/input-event-codes.h>
# ----------------------------------------------------------------------------
EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03
EV_MSC = 0x04
EV_SW = 0x05
EV_LED = 0x11
EV_REP = 0x14
EV_MAX = 0x1F

SYN_REPORT = 0

REL_X = 0x00
REL_Y = 0x01
REL_HWHEEL = 0x06
REL_WHEEL = 0x08
REL_WHEEL_HI_RES = 0x0B
REL_HWHEEL_HI_RES = 0x0C
REL_MAX = 0x0F

ABS_X = 0x00
ABS_Y = 0x01
ABS_MAX = 0x3F

LED_NUML = 0x00
LED_CAPSL = 0x01
LED_SCROLLL = 0x02
LED_COMPOSE = 0x03
LED_KANA = 0x04
LED_MAX = 0x0F

KEY_MAX = 0x2FF

BTN_MOUSE = 0x110
BTN_LEFT = 0x110
BTN_RIGHT = 0x111
BTN_MIDDLE = 0x112
BTN_SIDE = 0x113
BTN_EXTRA = 0x114
BTN_FORWARD = 0x115
BTN_BACK = 0x116
BTN_TASK = 0x117
BTN_TOUCH = 0x14A
BTN_TOOL_PEN = 0x140

BUS_USB = 0x03

# ----------------------------------------------------------------------------
# ioctl encoding (asm-generic, valid for arm, arm64 and x86)
# ----------------------------------------------------------------------------
_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = 8
_IOC_SIZESHIFT = 16
_IOC_DIRSHIFT = 30
_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2


def _IOC(direction: int, typ: str, nr: int, size: int) -> int:
    return (
        (direction << _IOC_DIRSHIFT)
        | (ord(typ) << _IOC_TYPESHIFT)
        | (nr << _IOC_NRSHIFT)
        | (size << _IOC_SIZESHIFT)
    )


def _IOR(typ: str, nr: int, size: int) -> int:
    return _IOC(_IOC_READ, typ, nr, size)


def _IOW(typ: str, nr: int, size: int) -> int:
    return _IOC(_IOC_WRITE, typ, nr, size)


EVIOCGVERSION = _IOR("E", 0x01, 4)
EVIOCGID = _IOR("E", 0x02, 8)


def EVIOCGNAME(length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x06, length)


def EVIOCGPHYS(length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x07, length)


def EVIOCGUNIQ(length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x08, length)


def EVIOCGLED(length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x19, length)


def EVIOCGBIT(ev_type: int, length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x20 + ev_type, length)


def EVIOCGABS(abs_code: int) -> int:
    return _IOR("E", 0x40 + abs_code, 24)


EVIOCGRAB = _IOW("E", 0x90, 4)

# struct input_event { struct timeval time; __u16 type; __u16 code; __s32 value; }
# Native long sizes give 24 bytes on 64-bit and 16 bytes on 32-bit kernels.
INPUT_EVENT = struct.Struct("@llHHi")


@dataclass
class AbsInfo:
    value: int
    minimum: int
    maximum: int
    fuzz: int
    flat: int
    resolution: int

    @property
    def span(self) -> int:
        return max(1, self.maximum - self.minimum)


@dataclass
class DeviceIdentity:
    name: str
    phys: str
    uniq: str
    bustype: int
    vendor: int
    product: int
    version: int


def _bits_from_buffer(buf: bytes) -> set[int]:
    bits: set[int] = set()
    for byte_index, byte in enumerate(buf):
        if not byte:
            continue
        for bit in range(8):
            if byte & (1 << bit):
                bits.add(byte_index * 8 + bit)
    return bits


def list_event_nodes() -> list[str]:
    """Return /dev/input/event* paths sorted numerically."""
    try:
        names = os.listdir("/dev/input")
    except FileNotFoundError:
        return []
    nodes = []
    for name in names:
        if name.startswith("event") and name[5:].isdigit():
            nodes.append((int(name[5:]), f"/dev/input/{name}"))
    return [path for _, path in sorted(nodes)]


class InputDevice:
    """A single /dev/input/eventN device opened non-blocking."""

    def __init__(self, path: str):
        self.path = path
        # O_RDWR so LED state can be written back to the device.
        try:
            self.fd = os.open(path, os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC)
        except PermissionError:
            self.fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
        try:
            self.identity = self._read_identity()
            self.ev_bits = self._read_bits(0, EV_MAX)
            self.key_bits = self._read_bits(EV_KEY, KEY_MAX) if EV_KEY in self.ev_bits else set()
            self.rel_bits = self._read_bits(EV_REL, REL_MAX) if EV_REL in self.ev_bits else set()
            self.abs_bits = self._read_bits(EV_ABS, ABS_MAX) if EV_ABS in self.ev_bits else set()
            self.led_bits = self._read_bits(EV_LED, LED_MAX) if EV_LED in self.ev_bits else set()
            self.absinfo: dict[int, AbsInfo] = {}
            for code in (ABS_X, ABS_Y):
                if code in self.abs_bits:
                    self.absinfo[code] = self._read_absinfo(code)
        except Exception:
            os.close(self.fd)
            raise
        self.grabbed = False
        self._st = os.fstat(self.fd)

    # -- identity -----------------------------------------------------------
    def _read_string(self, request_fn, length: int = 256) -> str:
        buf = bytearray(length)
        try:
            n = fcntl.ioctl(self.fd, request_fn(length), buf)
        except OSError:
            return ""
        if isinstance(n, int) and n > 0:
            raw = bytes(buf[:n])
        else:
            raw = bytes(buf)
        return raw.split(b"\0", 1)[0].decode("utf-8", "replace")

    def _read_identity(self) -> DeviceIdentity:
        buf = bytearray(8)
        fcntl.ioctl(self.fd, EVIOCGID, buf)
        bustype, vendor, product, version = struct.unpack("HHHH", bytes(buf))
        return DeviceIdentity(
            name=self._read_string(EVIOCGNAME),
            phys=self._read_string(EVIOCGPHYS),
            uniq=self._read_string(EVIOCGUNIQ),
            bustype=bustype,
            vendor=vendor,
            product=product,
            version=version,
        )

    def _read_bits(self, ev_type: int, max_code: int) -> set[int]:
        length = max_code // 8 + 1
        buf = bytearray(length)
        fcntl.ioctl(self.fd, EVIOCGBIT(ev_type, length), buf)
        return _bits_from_buffer(bytes(buf))

    def _read_absinfo(self, code: int) -> AbsInfo:
        buf = bytearray(24)
        fcntl.ioctl(self.fd, EVIOCGABS(code), buf)
        return AbsInfo(*struct.unpack("iiiiii", bytes(buf)))

    # -- classification -----------------------------------------------------
    @property
    def name(self) -> str:
        return self.identity.name

    @property
    def is_keyboard(self) -> bool:
        # Any ordinary key (below BTN_MISC 0x100) makes the device usable as
        # a keyboard-like source; this also covers small macro keypads that
        # only expose function keys or digits.
        return any(1 <= code < 0x100 for code in self.key_bits)

    @property
    def is_mouse(self) -> bool:
        has_button = BTN_LEFT in self.key_bits or BTN_TOUCH in self.key_bits
        has_axis = REL_X in self.rel_bits or ABS_X in self.abs_bits
        return has_button and has_axis

    @property
    def has_abs_pointer(self) -> bool:
        return ABS_X in self.abs_bits and ABS_Y in self.abs_bits

    # -- control ------------------------------------------------------------
    def grab(self) -> None:
        if not self.grabbed:
            fcntl.ioctl(self.fd, EVIOCGRAB, 1)
            self.grabbed = True

    def ungrab(self) -> None:
        if self.grabbed:
            try:
                fcntl.ioctl(self.fd, EVIOCGRAB, 0)
            except OSError:
                pass
            self.grabbed = False

    def read_events(self) -> list[tuple[int, int, int]]:
        """Drain pending events. Returns [] if nothing is available.

        Raises OSError (ENODEV) when the device has been unplugged.
        """
        events: list[tuple[int, int, int]] = []
        size = INPUT_EVENT.size
        while True:
            try:
                data = os.read(self.fd, size * 64)
            except BlockingIOError:
                break
            if not data:
                raise OSError(os.strerror(19), 19)  # ENODEV
            for offset in range(0, len(data) - size + 1, size):
                _sec, _usec, ev_type, code, value = INPUT_EVENT.unpack_from(data, offset)
                events.append((ev_type, code, value))
            if len(data) < size * 64:
                break
        return events

    def set_led(self, led_code: int, on: bool) -> None:
        if led_code not in self.led_bits:
            return
        payload = INPUT_EVENT.pack(0, 0, EV_LED, led_code, 1 if on else 0)
        payload += INPUT_EVENT.pack(0, 0, EV_SYN, SYN_REPORT, 0)
        try:
            os.write(self.fd, payload)
        except OSError:
            pass

    def close(self) -> None:
        if self.fd >= 0:
            self.ungrab()
            try:
                os.close(self.fd)
            finally:
                self.fd = -1

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        ident = self.identity
        return (
            f"InputDevice({self.path!r}, name={ident.name!r}, "
            f"id={ident.vendor:04x}:{ident.product:04x}, kbd={self.is_keyboard}, mouse={self.is_mouse})"
        )
