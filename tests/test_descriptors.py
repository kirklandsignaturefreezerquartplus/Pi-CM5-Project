import unittest

from hid_bridge.descriptors import (
    KEYBOARD_REPORT_LENGTH,
    keyboard_report_descriptor,
    mouse_report_descriptor,
    mouse_report_length,
    report_bit_sizes,
)

# HID 1.11 Appendix E.6 boot keyboard descriptor, byte for byte.
SPEC_BOOT_KEYBOARD = bytes.fromhex(
    "05010906a101050719e029e71500250175019508810295017508810195057501"
    "050819012905910295017503910195067508150025650507190029658100c0"
)


class DescriptorTests(unittest.TestCase):
    def test_boot_keyboard_matches_spec(self):
        desc = keyboard_report_descriptor(extended=False)
        self.assertEqual(len(desc), 63)
        self.assertEqual(desc, SPEC_BOOT_KEYBOARD)

    def test_keyboard_report_sizes(self):
        for extended in (False, True):
            in_bits, out_bits = report_bit_sizes(keyboard_report_descriptor(extended))
            self.assertEqual(in_bits, KEYBOARD_REPORT_LENGTH * 8)
            self.assertEqual(out_bits, 8)

    def test_extended_keyboard_widens_array(self):
        desc = keyboard_report_descriptor(extended=True)
        self.assertIn(bytes([0x26, 0xFF, 0x00]), desc)
        self.assertIn(bytes([0x2A, 0xFF, 0x00]), desc)
        self.assertEqual(len(desc), 65)

    def test_mouse_relative(self):
        for buttons in (3, 5):
            desc = mouse_report_descriptor("relative", buttons)
            in_bits, out_bits = report_bit_sizes(desc)
            self.assertEqual(in_bits, mouse_report_length("relative") * 8)
            self.assertEqual(out_bits, 0)
            # boot mouse compatible: first three bytes are buttons, X, Y
            self.assertEqual(desc[:6], bytes([0x05, 0x01, 0x09, 0x02, 0xA1, 0x01]))

    def test_mouse_absolute(self):
        desc = mouse_report_descriptor("absolute", 3)
        in_bits, _ = report_bit_sizes(desc)
        self.assertEqual(in_bits, mouse_report_length("absolute") * 8)
        self.assertIn(bytes([0x26, 0xFF, 0x7F]), desc)

    def test_bad_arguments(self):
        with self.assertRaises(ValueError):
            mouse_report_descriptor("relative", 4)
        with self.assertRaises(ValueError):
            mouse_report_descriptor("hover", 3)
        with self.assertRaises(ValueError):
            mouse_report_length("hover")

    def test_parser_rejects_report_ids(self):
        with self.assertRaises(ValueError):
            report_bit_sizes(bytes([0x85, 0x01]))
        with self.assertRaises(ValueError):
            report_bit_sizes(bytes([0xA1, 0x01]))  # unbalanced


if __name__ == "__main__":
    unittest.main()
