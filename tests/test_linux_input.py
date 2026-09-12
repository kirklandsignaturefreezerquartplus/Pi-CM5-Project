import struct
import unittest

from hid_bridge import linux_input as li


class IoctlTests(unittest.TestCase):
    def test_known_ioctl_numbers(self):
        # Values from <linux/input.h> on a 64-bit kernel.
        self.assertEqual(li.EVIOCGVERSION, 0x80044501)
        self.assertEqual(li.EVIOCGID, 0x80084502)
        self.assertEqual(li.EVIOCGNAME(256), 0x81004506)
        self.assertEqual(li.EVIOCGBIT(0, 4), 0x80044520)
        self.assertEqual(li.EVIOCGBIT(li.EV_KEY, 96), 0x80604521)
        self.assertEqual(li.EVIOCGABS(li.ABS_X), 0x80184540)
        self.assertEqual(li.EVIOCGRAB, 0x40044590)

    def test_input_event_struct_size(self):
        long_size = struct.calcsize("l")
        self.assertEqual(li.INPUT_EVENT.size, 2 * long_size + 8)

    def test_bits_from_buffer(self):
        self.assertEqual(li._bits_from_buffer(bytes([0b00000101, 0b10000000])), {0, 2, 15})
        self.assertEqual(li._bits_from_buffer(b"\x00\x00"), set())

    def test_absinfo_span(self):
        info = li.AbsInfo(0, 0, 32767, 0, 0, 0)
        self.assertEqual(info.span, 32767)
        self.assertEqual(li.AbsInfo(0, 5, 5, 0, 0, 0).span, 1)


if __name__ == "__main__":
    unittest.main()
