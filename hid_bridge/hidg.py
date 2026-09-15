"""Writers for the /dev/hidgN character devices created by usb_f_hid.

Besides sending input reports this module keeps usb_f_hid's GET_REPORT cache
current (kernel >= 6.10, ``GADGET_HID_WRITE_GET_REPORT``).  A real keyboard
answers ``GET_REPORT(Input)`` on the control endpoint with its current state;
without the cache the kernel would wait 2.5 s and then answer with zeros.
"""
from __future__ import annotations

import errno
import fcntl
import logging
import os
import select
import struct
import time

log = logging.getLogger("hid-bridge.hidg")

# Errors that mean "the host is not there right now" rather than a bug.
_DISCONNECT_ERRNOS = {errno.ESHUTDOWN, errno.ENODEV, errno.EPIPE, errno.ECONNRESET}

# <linux/usb/g_hid.h>
#   struct usb_hidg_report { __u8 report_id; __u8 userspace_req; __u16 length;
#                            __u8 data[64]; __u8 padding[4]; };
#   #define GADGET_HID_WRITE_GET_REPORT _IOW('g', 0x42, struct usb_hidg_report)
HIDG_MAX_REPORT_LENGTH = 64
USB_HIDG_REPORT = struct.Struct("=BBH64s4s")
GADGET_HID_WRITE_GET_REPORT = (1 << 30) | (USB_HIDG_REPORT.size << 16) | (ord("g") << 8) | 0x42

BACKOFF_MIN = 0.05
BACKOFF_MAX = 1.0


class HidgDevice:
    def __init__(self, path: str, report_length: int, label: str, idle_report: bytes | None = None):
        if report_length > HIDG_MAX_REPORT_LENGTH:
            raise ValueError("report_length exceeds usb_f_hid's 64-byte GET_REPORT limit")
        self.path = path
        self.report_length = report_length
        self.label = label
        self.idle_report = idle_report if idle_report is not None else bytes(report_length)
        self.fd = -1
        self._rdev = 0
        self.last_report: bytes | None = None
        self.last_sent_at = 0.0
        self.sent = 0
        self.dropped = 0
        self.deferred = 0
        self.disconnected = False
        # usb_f_hid marks the function "disabled" when the host de-configures
        # us; from then on its poll() reports readable forever and read()
        # fails with ENOMEM (SET_REPORT path) or ESHUTDOWN (interrupt OUT
        # path), so the bridge must stop polling the fd for reads until the
        # host configures us again.
        self.host_disabled = False
        # While the host has suspended the bus, dwc2 refuses every queued
        # request (-EAGAIN) although poll() reports the fd writable.  The
        # bridge detects that pattern and retries with a growing delay
        # instead of spinning; ``suspended_path`` (libcomposite's sysfs
        # attribute) lets it wait without even trying while suspended.
        self.suspended_path = ""
        self.backoff_until = 0.0
        self._backoff = 0.0
        self._warned_disconnected = False
        self._warned_backoff = False
        self._get_report_supported = True
        self._cached_get_report: bytes | None = None

    # -- lifecycle -------------------------------------------------------------
    def open(self) -> None:
        if self.fd < 0:
            self.fd = os.open(self.path, os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC)
            self._rdev = os.fstat(self.fd).st_rdev
            self._cached_get_report = None
            self.cache_get_report(self.idle_report)

    def close(self) -> None:
        if self.fd >= 0:
            try:
                os.close(self.fd)
            finally:
                self.fd = -1

    def revalidate(self) -> bool:
        """Reopen if /dev/hidgN was recreated (gadget torn down and rebuilt).

        Returns True when the device node changed.
        """
        if self.fd < 0:
            return False
        try:
            rdev = os.stat(self.path).st_rdev
        except FileNotFoundError:
            rdev = 0
        if rdev == self._rdev:
            return False
        log.warning("%s: %s was recreated; reopening", self.label, self.path)
        self.close()
        self.last_report = None
        self.disconnected = True
        try:
            self.open()
        except OSError as exc:
            log.warning("%s: cannot reopen %s: %s", self.label, self.path, exc.strerror)
        return True

    @property
    def poll_readable(self) -> bool:
        """Whether the bridge should select() this fd for output reports."""
        return self.fd >= 0 and not self.host_disabled

    def host_state_changed(self, udc_state: str) -> None:
        """Re-arm reads once the UDC reports the host configured us again."""
        if self.host_disabled and udc_state == "configured":
            log.info("%s: host configured the interface again", self.label)
            self.host_disabled = False

    def host_suspended(self) -> bool:
        """libcomposite's view of bus suspend (poll-only sysfs attribute)."""
        if not self.suspended_path:
            return False
        try:
            with open(self.suspended_path) as fh:
                return fh.read().strip() == "1"
        except OSError:
            return False

    def enter_backoff(self, now: float) -> None:
        """A write failed although the fd was writable: the bus is suspended."""
        self._backoff = min(max(self._backoff * 2, BACKOFF_MIN), BACKOFF_MAX)
        self.backoff_until = now + self._backoff
        if not self._warned_backoff:
            log.info("%s: host is not accepting reports (bus suspended?); retrying with backoff", self.label)
            self._warned_backoff = True

    def extend_backoff(self, now: float, seconds: float = 0.25) -> None:
        self.backoff_until = now + seconds

    def _clear_backoff(self) -> None:
        if self._warned_backoff:
            log.info("%s: host accepting reports again", self.label)
        self._backoff = 0.0
        self.backoff_until = 0.0
        self._warned_backoff = False

    # -- GET_REPORT cache -------------------------------------------------------
    def cache_get_report(self, report: bytes) -> None:
        """Publish ``report`` as the answer to GET_REPORT(Input) on EP0."""
        if not self._get_report_supported or self.fd < 0 or report == self._cached_get_report:
            return
        payload = USB_HIDG_REPORT.pack(0, 0, len(report), report.ljust(HIDG_MAX_REPORT_LENGTH, b"\0"), b"\0" * 4)
        try:
            fcntl.ioctl(self.fd, GADGET_HID_WRITE_GET_REPORT, payload)
        except OSError as exc:
            if exc.errno in (errno.ENOTTY, errno.EINVAL):
                self._get_report_supported = False
                log.info("%s: kernel lacks the f_hid GET_REPORT cache ioctl; the kernel answers GET_REPORT itself", self.label)
            else:
                log.warning("%s: GET_REPORT cache update failed: %s", self.label, exc.strerror)
            return
        self._cached_get_report = report

    # -- input reports ----------------------------------------------------------
    def write_report(self, report: bytes, force: bool = False, get_report: bytes | None = None) -> bool:
        """Try to send ``report`` once, without blocking.

        Returns True when the report was handed to the kernel (or was
        identical to the last one and ``force`` is not set).  Returns False
        when it could not go out right now: either the previous report is
        still waiting for the host to poll (``usb_f_hid`` keeps exactly one
        IN request in flight; the fd becomes writable once it completes),
        the bus is suspended, or the host is not connected.  The caller
        keeps its own "latest state" and retries when the fd is writable,
        which is how a real keyboard or mouse behaves: one report register,
        latest state wins, motion accumulates between polls.

        ``get_report`` overrides what GET_REPORT should answer from now on;
        it defaults to ``report`` (correct for state-based reports).
        """
        if len(report) != self.report_length:
            raise ValueError(f"{self.label}: report must be {self.report_length} bytes, got {len(report)}")
        if self.fd < 0:
            try:
                self.open()
            except OSError as exc:
                self._note_disconnect(exc)
                self.dropped += 1
                return False
        self.cache_get_report(report if get_report is None else get_report)
        if not force and report == self.last_report:
            return True
        try:
            os.write(self.fd, report)
        except BlockingIOError:
            # Previous report not yet collected by the host, or bus suspended.
            self.deferred += 1
            return False
        except OSError as exc:
            self.dropped += 1
            if exc.errno in _DISCONNECT_ERRNOS:
                self._note_disconnect(exc)
                return False
            raise
        self.last_report = report
        self.last_sent_at = time.monotonic()
        self.sent += 1
        if self.backoff_until or self._backoff:
            self._clear_backoff()
        if self.disconnected or self.host_disabled:
            log.info("%s: host connected again", self.label)
            self.disconnected = False
            self.host_disabled = False
            self._warned_disconnected = False
        return True

    def write_report_blocking(self, report: bytes, timeout: float) -> bool:
        """Best-effort delivery with a bounded wait; used only at shutdown."""
        deadline = time.monotonic() + timeout
        while True:
            if self.write_report(report, force=True):
                return True
            if self.disconnected or self.host_disabled or self.fd < 0:
                return False
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            try:
                select.select([], [self.fd], [], min(remaining, 0.02))
            except OSError:
                return False

    def _note_disconnect(self, exc: OSError) -> None:
        self.disconnected = True
        self.last_report = None
        if not self._warned_disconnected:
            log.warning("%s: host not connected (%s); reports are dropped until it enumerates us", self.label, exc.strerror)
            self._warned_disconnected = True

    # -- output reports (LEDs) ---------------------------------------------------
    def read_output_report(self) -> bytes | None:
        """Read a pending output report (keyboard LED byte). None if nothing is pending."""
        if self.fd < 0:
            return None
        try:
            data = os.read(self.fd, HIDG_MAX_REPORT_LENGTH)
        except BlockingIOError:
            return None
        except OSError as exc:
            if exc.errno == errno.ENOMEM or exc.errno in _DISCONNECT_ERRNOS:
                # usb_f_hid's "function disabled" signal: the host went away.
                if not self.host_disabled:
                    log.info("%s: host de-configured the interface; waiting for it to come back", self.label)
                self.host_disabled = True
                self.disconnected = True
                self.last_report = None
                return None
            raise
        return data or None

    def stats(self) -> dict:
        return {
            "device": self.path,
            "sent": self.sent,
            "deferred": self.deferred,
            "dropped": self.dropped,
            "host_connected": not (self.disconnected or self.host_disabled),
            "backing_off": self.backoff_until > 0,
            "get_report_cache": self._get_report_supported,
        }
