import unittest

from hid_bridge import linux_input as li
from hid_bridge.reports import (
    absolute_mouse_report,
    keyboard_report,
    relative_mouse_reports,
    scale_abs,
    split_delta,
)


class KeyboardReportTests(unittest.TestCase):
    def test_idle(self):
        self.assertEqual(keyboard_report([]), bytes(8))

    def test_modifiers_and_keys(self):
        report = keyboard_report({0xE0, 0xE2, 0x4C})  # ctrl + alt + delete
        self.assertEqual(report, bytes([0x05, 0x00, 0x4C, 0, 0, 0, 0, 0]))

    def test_six_keys_sorted(self):
        report = keyboard_report([0x09, 0x04, 0x05, 0x06, 0x07, 0x08])
        self.assertEqual(report[2:], bytes([0x04, 0x05, 0x06, 0x07, 0x08, 0x09]))

    def test_rollover_phantom(self):
        report = keyboard_report(range(0x04, 0x0B))  # 7 keys
        self.assertEqual(report, bytes([0x00, 0x00] + [0x01] * 6))

    def test_boot_descriptor_range_drops_high_usages(self):
        report = keyboard_report({0x68, 0x04}, max_array_usage=0x65)  # F13 dropped
        self.assertEqual(report[2:], bytes([0x04, 0, 0, 0, 0, 0]))
        report = keyboard_report({0x68, 0x04}, max_array_usage=0xFF)
        self.assertEqual(report[2:], bytes([0x04, 0x68, 0, 0, 0, 0]))

    def test_modifier_only(self):
        self.assertEqual(keyboard_report({0xE1})[0], 0x02)
        self.assertEqual(keyboard_report({0xE7})[0], 0x80)


class MouseReportTests(unittest.TestCase):
    def test_split_delta(self):
        self.assertEqual(list(split_delta(5)), [5])
        self.assertEqual(list(split_delta(127)), [127])
        self.assertEqual(list(split_delta(128)), [127, 1])
        self.assertEqual(list(split_delta(-300)), [-127, -127, -46])
        self.assertEqual(list(split_delta(0)), [0])

    def test_relative_single(self):
        reports = relative_mouse_reports(0b101, 10, -3, 1, 3)
        self.assertEqual(reports, [bytes([0x05, 10, 0xFD, 1])])

    def test_relative_button_mask(self):
        reports = relative_mouse_reports(0b11111, 0, 0, 0, 3)
        self.assertEqual(reports[0][0], 0b111)
        reports = relative_mouse_reports(0b11111, 0, 0, 0, 5)
        self.assertEqual(reports[0][0], 0b11111)

    def test_relative_large_motion_split(self):
        reports = relative_mouse_reports(0, 300, -130, 0, 3)
        self.assertEqual(len(reports), 3)
        total_x = sum(int.from_bytes(r[1:2], "little", signed=True) for r in reports)
        total_y = sum(int.from_bytes(r[2:3], "little", signed=True) for r in reports)
        self.assertEqual((total_x, total_y), (300, -130))

    def test_absolute(self):
        report = absolute_mouse_report(1, 0x1234, 0x7FFF, -2, 3)
        self.assertEqual(report, bytes([0x01, 0x34, 0x12, 0xFF, 0x7F, 0xFE]))
        self.assertEqual(absolute_mouse_report(0, 99999, -5, 0, 3), bytes([0, 0xFF, 0x7F, 0, 0, 0]))

    def test_scale_abs(self):
        self.assertEqual(scale_abs(0, 0, 32767), 0)
        self.assertEqual(scale_abs(32767, 0, 32767), 32767)
        self.assertEqual(scale_abs(50, 0, 100), 16384)
        self.assertEqual(scale_abs(1919, 0, 1919, 1919), 1919)

    def test_button_bits(self):
        from hid_bridge.reports import BUTTON_BITS
        self.assertEqual(BUTTON_BITS[li.BTN_LEFT], 0)
        self.assertEqual(BUTTON_BITS[li.BTN_RIGHT], 1)
        self.assertEqual(BUTTON_BITS[li.BTN_MIDDLE], 2)
        self.assertEqual(BUTTON_BITS[li.BTN_SIDE], BUTTON_BITS[li.BTN_BACK])
        self.assertEqual(BUTTON_BITS[li.BTN_EXTRA], BUTTON_BITS[li.BTN_FORWARD])


if __name__ == "__main__":
    unittest.main()
