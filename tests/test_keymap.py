import unittest

from hid_bridge import keymap
from hid_bridge.keymap import EVDEV_TO_HID, KEY_ALIASES, KEY_CODES, US_LAYOUT, usage_from_name


class KeymapTests(unittest.TestCase):
    def test_key_codes_unique(self):
        self.assertEqual(len(KEY_CODES), len(set(KEY_CODES.values())))

    def test_letters_digits_and_modifiers(self):
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_A"]], 0x04)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_Z"]], 0x1D)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_1"]], 0x1E)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_0"]], 0x27)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_ENTER"]], 0x28)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_LEFTCTRL"]], 0xE0)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_RIGHTMETA"]], 0xE7)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_F12"]], 0x45)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_F24"]], 0x73)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_KPENTER"]], 0x58)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_102ND"]], 0x64)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_YEN"]], 0x89)

    def test_all_usages_in_keyboard_page_range(self):
        for code, usage in EVDEV_TO_HID.items():
            self.assertIn(code, keymap.CODE_NAMES)
            self.assertTrue(0x04 <= usage <= 0xE7, f"{keymap.CODE_NAMES[code]} -> {usage:#x}")

    def test_usages_unique_except_documented_duplicates(self):
        seen = {}
        for code, usage in EVDEV_TO_HID.items():
            seen.setdefault(usage, []).append(keymap.CODE_NAMES[code])
        dupes = {u: names for u, names in seen.items() if len(names) > 1}
        # KEY_COMPOSE and KEY_MENU both mean the Application key.
        self.assertEqual(dupes, {0x65: ["KEY_COMPOSE", "KEY_MENU"]})

    def test_aliases_resolve(self):
        self.assertEqual(usage_from_name("ctrl"), 0xE0)
        self.assertEqual(usage_from_name("Delete"), 0x4C)
        self.assertEqual(usage_from_name("KEY_DELETE"), 0x4C)
        self.assertEqual(usage_from_name("f13"), 0x68)
        self.assertEqual(usage_from_name("f12"), 0x45)
        self.assertEqual(usage_from_name("0x3a"), 0x3A)
        self.assertEqual(usage_from_name("a"), 0x04)
        self.assertEqual(usage_from_name("0"), 0x27)
        with self.assertRaises(KeyError):
            usage_from_name("notakey")
        with self.assertRaises(KeyError):
            usage_from_name("KEY_WLAN")  # not on the keyboard page

    def test_alias_targets_valid(self):
        for name, usage in KEY_ALIASES.items():
            self.assertTrue(0x04 <= usage <= 0xE7, name)

    def test_us_layout_round_trip(self):
        self.assertEqual(US_LAYOUT["a"], (0x04, False))
        self.assertEqual(US_LAYOUT["A"], (0x04, True))
        self.assertEqual(US_LAYOUT["!"], (0x1E, True))
        self.assertEqual(US_LAYOUT[")"], (0x27, True))
        self.assertEqual(US_LAYOUT["\n"], (0x28, False))
        self.assertEqual(US_LAYOUT["?"], (0x38, True))
        printable = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !@#$%^&*()-_=+[]{}\\|;:'\",<.>/?`~\t\n"
        for ch in printable:
            self.assertIn(ch, US_LAYOUT)


if __name__ == "__main__":
    unittest.main()
