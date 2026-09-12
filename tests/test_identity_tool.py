import importlib.util
import os
import random
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("identity_tool", os.path.join(ROOT, "tools", "identity-from-lsusb.py"))
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

SAMPLE = """
Bus 001 Device 004: ID 1a2c:2d43 China Resource Semico Co., Ltd USB Keyboard
Device Descriptor:
  bLength                18
  bDescriptorType         1
  bcdUSB               1.10
  bDeviceClass            0
  bMaxPacketSize0         8
  idVendor           0x1a2c China Resource Semico Co., Ltd
  idProduct          0x2d43
  bcdDevice            1.10
  iManufacturer           1 SEMICO
  iProduct                2 USB Keyboard
  iSerial                 0
  bNumConfigurations      1
  Configuration Descriptor:
    bmAttributes         0xa0
      (Bus Powered)
      Remote Wakeup
    MaxPower               98mA
"""

SAMPLE_SERIAL = SAMPLE.replace("iSerial                 0", "iSerial                 3 AB12CD34")


class IdentityToolTests(unittest.TestCase):
    def test_conversion(self):
        out = tool.convert(SAMPLE)
        self.assertIn("vendor_id = 0x1a2c", out)
        self.assertIn("product_id = 0x2d43", out)
        self.assertIn("device_version = 0x0110", out)
        self.assertIn('manufacturer = "SEMICO"', out)
        self.assertIn('product = "USB Keyboard"', out)
        self.assertIn('serial = ""', out)
        self.assertIn("remote_wakeup = true", out)
        self.assertIn("self_powered = false", out)
        self.assertIn("max_power_ma = 98", out)
        self.assertIn("# reference has no serial", out)

    def test_serial_randomised_same_shape(self):
        out = tool.convert(SAMPLE_SERIAL, random.Random(1))
        line = [l for l in out.splitlines() if l.startswith("serial")][0]
        value = line.split('"')[1]
        self.assertEqual(len(value), 8)
        self.assertNotEqual(value, "AB12CD34")
        self.assertTrue(value[0].isalpha() and value[2].isdigit())

    def test_output_is_valid_toml(self):
        import tomllib
        data = tomllib.loads(tool.convert(SAMPLE_SERIAL))
        self.assertEqual(data["gadget"]["vendor_id"], 0x1A2C)


if __name__ == "__main__":
    unittest.main()
