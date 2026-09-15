import errno
import os
import unittest
from unittest import mock

from hid_bridge import hidg
from hid_bridge.hidg import GADGET_HID_WRITE_GET_REPORT, USB_HIDG_REPORT, HidgDevice


class HidgIoctlTests(unittest.TestCase):
    def test_struct_and_ioctl_number(self):
        # sizeof(struct usb_hidg_report) == 72 -> _IOW('g', 0x42, 72)
        self.assertEqual(USB_HIDG_REPORT.size, 72)
        self.assertEqual(GADGET_HID_WRITE_GET_REPORT, 0x40486742)

    def test_cache_get_report_payload(self):
        dev = HidgDevice("/dev/null", 8, "kbd")
        calls = []

        def fake_ioctl(fd, request, payload):
            calls.append((request, bytes(payload)))
            return 0

        with mock.patch.object(hidg.fcntl, "ioctl", side_effect=fake_ioctl):
            dev.open()
            report = bytes([0x02, 0, 0x04, 0, 0, 0, 0, 0])
            dev.write_report(report)
            dev.write_report(report)  # identical: no second ioctl
        try:
            self.assertEqual(len(calls), 2)  # idle report at open + one update
            request, payload = calls[1]
            self.assertEqual(request, GADGET_HID_WRITE_GET_REPORT)
            report_id, userspace_req, length, data, padding = USB_HIDG_REPORT.unpack(payload)
            self.assertEqual((report_id, userspace_req, length), (0, 0, 8))
            self.assertEqual(data[:8], report)
            self.assertEqual(data[8:], bytes(56))
            self.assertEqual(dev.stats()["get_report_cache"], True)
        finally:
            dev.close()

    def test_cache_disabled_on_old_kernel(self):
        dev = HidgDevice("/dev/null", 4, "mouse")
        with mock.patch.object(hidg.fcntl, "ioctl", side_effect=OSError(errno.ENOTTY, "no ioctl")) as ioctl:
            dev.open()
            dev.write_report(bytes([1, 0, 0, 0]))
            dev.write_report(bytes([0, 0, 0, 0]))
        try:
            self.assertEqual(ioctl.call_count, 1)
            self.assertFalse(dev.stats()["get_report_cache"])
        finally:
            dev.close()


class HidgHostStateTests(unittest.TestCase):
    def make(self):
        dev = HidgDevice("/dev/null", 8, "kbd")
        with mock.patch.object(hidg.fcntl, "ioctl", side_effect=OSError(errno.ENOTTY, "x")):
            dev.open()
        self.addCleanup(dev.close)
        return dev

    def test_dedup_and_force(self):
        dev = self.make()
        r = bytes([0, 0, 4, 0, 0, 0, 0, 0])
        self.assertTrue(dev.write_report(r))
        self.assertTrue(dev.write_report(r))
        self.assertEqual(dev.sent, 1)
        self.assertTrue(dev.write_report(r, force=True))
        self.assertEqual(dev.sent, 2)
        with self.assertRaises(ValueError):
            dev.write_report(bytes(3))

    def test_disabled_function_stops_read_polling(self):
        dev = self.make()
        self.assertTrue(dev.poll_readable)
        with mock.patch.object(hidg.os, "read", side_effect=OSError(errno.ENOMEM, "disabled")):
            self.assertIsNone(dev.read_output_report())
        self.assertTrue(dev.host_disabled)
        self.assertFalse(dev.poll_readable)
        self.assertFalse(dev.stats()["host_connected"])
        dev.host_state_changed("default")
        self.assertFalse(dev.poll_readable)
        dev.host_state_changed("configured")
        self.assertTrue(dev.poll_readable)

    def test_successful_write_clears_disabled(self):
        dev = self.make()
        dev.host_disabled = True
        dev.write_report(bytes([0, 0, 4, 0, 0, 0, 0, 0]))
        self.assertFalse(dev.host_disabled)

    def test_eagain_defers_without_dropping(self):
        dev = self.make()
        with mock.patch.object(hidg.os, "write", side_effect=BlockingIOError()):
            self.assertFalse(dev.write_report(bytes([0, 0, 4, 0, 0, 0, 0, 0])))
        self.assertEqual((dev.deferred, dev.dropped, dev.sent), (1, 0, 0))
        self.assertIsNone(dev.last_report)
        self.assertFalse(dev.disconnected)

    def test_eshutdown_is_a_disconnect(self):
        dev = self.make()
        with mock.patch.object(hidg.os, "write", side_effect=OSError(errno.ESHUTDOWN, "shutdown")):
            self.assertFalse(dev.write_report(bytes([0, 0, 4, 0, 0, 0, 0, 0])))
        self.assertTrue(dev.disconnected)
        self.assertEqual(dev.dropped, 1)
        self.assertIsNone(dev.last_report)

    def test_unexpected_errors_propagate(self):
        dev = self.make()
        with mock.patch.object(hidg.os, "write", side_effect=OSError(errno.EIO, "io")):
            with self.assertRaises(OSError):
                dev.write_report(bytes(8))

    def test_read_output_report_plain(self):
        dev = self.make()
        with mock.patch.object(hidg.os, "read", return_value=b"\x03"):
            self.assertEqual(dev.read_output_report(), b"\x03")
        with mock.patch.object(hidg.os, "read", side_effect=BlockingIOError()):
            self.assertIsNone(dev.read_output_report())


if __name__ == "__main__":
    unittest.main()
