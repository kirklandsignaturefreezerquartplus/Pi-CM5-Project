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

SAMPLE_TOPOLOGY = SAMPLE + """
    Interface Descriptor:
      bLength                 9
      bDescriptorType         4
      bInterfaceNumber        0
      bAlternateSetting       0
      bNumEndpoints           1
      bInterfaceClass         3 Human Interface Device
      bInterfaceSubClass      1 Boot Interface Subclass
      bInterfaceProtocol      1 Keyboard
      iInterface              0
        HID Device Descriptor:
          bLength                 9
          bDescriptorType        33
          bcdHID               1.10
          bCountryCode            0 Not supported
          bNumDescriptors         1
          bDescriptorType        34 Report
          wDescriptorLength      65
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x81  EP 1 IN
        bmAttributes            3
          Transfer Type            Interrupt
        wMaxPacketSize     0x0008  1x 8 bytes
        bInterval               8
    Interface Descriptor:
      bLength                 9
      bDescriptorType         4
      bInterfaceNumber        1
      bAlternateSetting       0
      bNumEndpoints           2
      bInterfaceClass         3 Human Interface Device
      bInterfaceSubClass      0
      bInterfaceProtocol      0
      iInterface              0
        HID Device Descriptor:
          bLength                 9
          bDescriptorType        33
          bcdHID               1.10
          bCountryCode            0 Not supported
          bNumDescriptors         1
          bDescriptorType        34 Report
          wDescriptorLength     120
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x82  EP 2 IN
        bmAttributes            3
          Transfer Type            Interrupt
        wMaxPacketSize     0x0010  1x 16 bytes
        bInterval              10
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x02  EP 2 OUT
        bmAttributes            3
          Transfer Type            Interrupt
        wMaxPacketSize     0x0010  1x 16 bytes
        bInterval              10
    Interface Descriptor:
      bLength                 9
      bDescriptorType         4
      bInterfaceNumber        2
      bAlternateSetting       0
      bNumEndpoints           1
      bInterfaceClass         3 Human Interface Device
      bInterfaceSubClass      0
      bInterfaceProtocol      0
      iInterface              0
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x83  EP 3 IN
        bmAttributes            3
          Transfer Type            Interrupt
        wMaxPacketSize     0x0008  1x 8 bytes
        bInterval               8
"""


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

    def test_topology_warnings(self):
        out = tool.convert(SAMPLE_TOPOLOGY)
        self.assertIn("bcdUSB is 1.10", out)
        self.assertIn("bMaxPacketSize0 is 8", out)
        self.assertIn("reference has 3 interface(s)", out)
        self.assertIn("interface 0: reference polls every 8 ms", out)
        self.assertIn("interface 0: reference report descriptor is 65 bytes", out)
        self.assertIn("interface 1: reference class/subclass/protocol (3, 0, 0)", out)
        self.assertIn("interface 1: reference has 2 endpoint(s)", out)
        self.assertIn("bcdHID 1.10", out)
        self.assertIn("A descriptor dump of the clone will differ", out)
        import tomllib
        tomllib.loads(out)   # warnings are comments; still valid TOML

    def test_no_interface_block_is_flagged(self):
        out = tool.convert(SAMPLE)
        self.assertIn("no interface descriptors found", out)

    def test_output_is_valid_toml(self):
        import tomllib
        data = tomllib.loads(tool.convert(SAMPLE_SERIAL))
        self.assertEqual(data["gadget"]["vendor_id"], 0x1A2C)


if __name__ == "__main__":
    unittest.main()
