"""Writers for the /dev/hidgN character devices created by usb_f_hid."""
from __future__ import annotations

import errno
import logging
import os
import select
import time

log = logging.getLogger("hid-bridge.hidg")

# Errors that mean "the host is not there right now" rather than a bug.
_DISCONNECT_ERRNOS = {errno.ESHUTDOWN, errno.ENODEV, errno.EPIPE, errno.ECONNRESET}


class HidgDevice:
    def __init__(self, path: str, report_length: int, label: str, write_timeout: float = 0.05):
        self.path = path
        self.report_length = report_length
        self.label = label
        self.write_timeout = write_timeout
        self.fd = -1
        self.last_report: bytes | None = None
        self.sent = 0
        self.dropped = 0
        self.disconnected = False
        self._warned_disconnected = False

    def open(self) -> None:
        if self.fd < 0:
            self.fd = os.open(self.path, os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC)

    def close(self) -> None:
        if self.fd >= 0:
            try:
                os.close(self.fd)
            finally:
                self.fd = -1

    def write_report(self, report: bytes, force: bool = False) -> bool:
        """Send ``report``; returns True on success.

        Identical consecutive reports are suppressed unless ``force`` is set
        (relative mouse reports must always go out because they carry motion).
        """
        if len(report) != self.report_length:
            raise ValueError(f"{self.label}: report must be {self.report_length} bytes, got {len(report)}")
        if not force and report == self.last_report:
            return True
        if self.fd < 0:
            try:
                self.open()
            except OSError as exc:
                self._note_disconnect(exc)
                self.dropped += 1
                return False
        deadline = time.monotonic() + self.write_timeout
        while True:
            try:
                os.write(self.fd, report)
                self.last_report = report
                self.sent += 1
                if self.disconnected:
                    log.info("%s: host connected again", self.label)
                    self.disconnected = False
                    self._warned_disconnected = False
                return True
            except BlockingIOError:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.dropped += 1
                    log.debug("%s: host not polling, report dropped", self.label)
                    return False
                select.select([], [self.fd], [], remaining)
            except OSError as exc:
                self.dropped += 1
                if exc.errno in _DISCONNECT_ERRNOS:
                    self._note_disconnect(exc)
                    return False
                raise

    def _note_disconnect(self, exc: OSError) -> None:
        self.disconnected = True
        self.last_report = None
        if not self._warned_disconnected:
            log.warning("%s: host not connected (%s); reports are dropped until it enumerates us", self.label, exc.strerror)
            self._warned_disconnected = True

    def read_output_report(self) -> bytes | None:
        """Read a pending output report (keyboard LED byte). None if nothing is pending."""
        if self.fd < 0:
            return None
        try:
            data = os.read(self.fd, 64)
        except BlockingIOError:
            return None
        except OSError as exc:
            if exc.errno in _DISCONNECT_ERRNOS or exc.errno == errno.EAGAIN:
                return None
            raise
        return data or None

    def stats(self) -> dict:
        return {
            "device": self.path,
            "sent": self.sent,
            "dropped": self.dropped,
            "host_connected": not self.disconnected,
        }
