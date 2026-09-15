import os
import tempfile
import tomllib
import unittest

from hid_bridge.config import ConfigError, load_config, parse_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ConfigTests(unittest.TestCase):
    def test_shipped_config_parses(self):
        cfg = load_config(os.path.join(ROOT, "config", "config.toml"))
        self.assertEqual(cfg.gadget.vendor_id, 0x1209)
        self.assertEqual(cfg.gadget.max_speed, "full-speed")
        self.assertEqual(cfg.keyboard.descriptor, "boot")
        self.assertEqual(cfg.mouse.mode, "relative")
        self.assertIn("ctrl_alt_del", cfg.macros)
        self.assertEqual(cfg.rule_for("Anything", "", 0, 0).role, "passthrough")

    def test_defaults(self):
        cfg = parse_config({})
        self.assertEqual(cfg.gadget.product, "USB Keyboard")
        self.assertEqual(cfg.bridge.control_socket, "/run/hid-bridge/ctl.sock")

    def test_hex_strings_and_rules(self):
        cfg = parse_config({
            "gadget": {"vendor_id": "0x046d", "product_id": 0xC52B},
            "inputs": [
                {"name": "^Macro", "vendor": "0x1a2c", "role": "macro", "bindings": {"key_1": "m"}},
                {"name": "Dell", "role": "ignore"},
            ],
            "macros": {"m": ["ctrl+c"]},
        })
        self.assertEqual(cfg.gadget.vendor_id, 0x046D)
        rule = cfg.rule_for("Macro Pad", "usb-1", 0x1A2C, 1)
        self.assertEqual(rule.role, "macro")
        self.assertEqual(rule.bindings, {"KEY_1": "m"})
        self.assertEqual(cfg.rule_for("Macro Pad", "usb-1", 0x9999, 1).role, "passthrough")
        self.assertEqual(cfg.rule_for("Dell KB216", "", 0, 0).role, "ignore")

    def test_errors(self):
        cases = [
            {"bogus": {}},
            {"gadget": {"vendor_id": 0x10000}},
            {"gadget": {"max_speed": "warp"}},
            {"gadget": {"unknown": 1}},
            {"keyboard": {"descriptor": "fancy"}},
            {"mouse": {"mode": "hover"}},
            {"mouse": {"buttons": 4}},
            {"mouse": {"abs_to_rel_resolution": [1]}},
            {"inputs": [{"role": "sometimes"}]},
            {"inputs": [{"name": "("}]},
            {"inputs": [{"bindings": {"KEY_1": "missing"}}]},
            {"inputs": [{"bindings": {"KEY_KP_0": "m"}}], "macros": {"m": ["a"]}},
            {"macros": {"bad": ["wait x"]}},
            {"macros": {"bad": 5}},
            {"bridge": {"log_level": "loud"}},
            {"mouse": {"rel_to_abs_gain": "17"}},
            {"mouse": {"rel_to_abs_gain": 0}},
            {"mouse": {"rel_to_abs_gain": True}},
        ]
        for data in cases:
            with self.assertRaises(ConfigError, msg=repr(data)):
                parse_config(data)

    def test_load_missing_and_invalid(self):
        with self.assertRaises(ConfigError):
            load_config("/nonexistent/config.toml")
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as fh:
            fh.write("[gadget\n")
        try:
            with self.assertRaises(ConfigError):
                load_config(fh.name)
        finally:
            os.unlink(fh.name)

    def test_shipped_config_is_valid_toml_with_commented_examples(self):
        with open(os.path.join(ROOT, "config", "config.toml"), "rb") as fh:
            data = tomllib.load(fh)
        self.assertNotIn("inputs", data)  # examples stay commented out


if __name__ == "__main__":
    unittest.main()
