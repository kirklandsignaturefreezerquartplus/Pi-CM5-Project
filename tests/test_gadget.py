"""Gadget configfs logic exercised against a temporary directory tree."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from hid_bridge import gadget as gadget_module
from hid_bridge.config import parse_config
from hid_bridge.gadget import Gadget, GadgetError


class GadgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.state_file = os.path.join(self.tmp, "state.json")
        self.cfg = parse_config({"gadget": {"configfs": os.path.join(self.tmp, "usb_gadget"),
                                            "manufacturer": "Acme", "product": "Keyboard", "serial": ""}})
        os.makedirs(self.cfg.gadget.configfs)
        patches = [
            mock.patch.object(gadget_module, "list_udcs", return_value=["fake.udc"]),
            mock.patch.object(gadget_module, "STATE_FILE", self.state_file),
            mock.patch.object(gadget_module, "STATE_DIR", self.tmp),
            mock.patch.object(Gadget, "resolve_devices", return_value={
                "keyboard": "/dev/hidg0", "mouse": "/dev/hidg1", "udc": "fake.udc",
                "gadget": "x", "keyboard_report_length": 8, "mouse_report_length": 4}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def read(self, *parts):
        with open(os.path.join(self.cfg.gadget.configfs, "hidbridge", *parts)) as fh:
            return fh.read()

    def test_up_writes_expected_tree(self):
        g = Gadget(self.cfg)
        devices = g.up()
        self.assertEqual(devices["keyboard"], "/dev/hidg0")
        root = os.path.join(self.cfg.gadget.configfs, "hidbridge")
        self.assertEqual(self.read("idVendor"), "0x1209")
        self.assertEqual(self.read("idProduct"), "0x0001")
        self.assertEqual(self.read("bcdUSB"), "0x0200")
        self.assertEqual(self.read("bMaxPacketSize0"), "0x40")
        self.assertEqual(self.read("bDeviceClass"), "0x00")
        self.assertEqual(self.read("strings", "0x409", "manufacturer"), "Acme")
        self.assertEqual(self.read("strings", "0x409", "product"), "Keyboard")
        self.assertFalse(os.path.exists(os.path.join(root, "strings", "0x409", "serialnumber")))
        self.assertTrue(any("serialnumber is empty" in w for w in g.warnings))
        self.assertEqual(self.read("configs", "c.1", "bmAttributes"), "0xa0")
        self.assertEqual(self.read("configs", "c.1", "MaxPower"), "100")
        self.assertEqual(self.read("functions", "hid.kbd", "protocol"), "1")
        self.assertEqual(self.read("functions", "hid.kbd", "subclass"), "1")
        self.assertEqual(self.read("functions", "hid.kbd", "report_length"), "8")
        self.assertEqual(self.read("functions", "hid.mouse", "protocol"), "2")
        self.assertEqual(self.read("functions", "hid.mouse", "report_length"), "4")
        with open(os.path.join(root, "functions", "hid.kbd", "report_desc"), "rb") as fh:
            self.assertEqual(len(fh.read()), 63)
        # interface order: keyboard linked first
        links = sorted(os.listdir(os.path.join(root, "configs", "c.1")))
        self.assertIn("hid.kbd", links)
        self.assertIn("hid.mouse", links)
        self.assertTrue(os.path.islink(os.path.join(root, "configs", "c.1", "hid.kbd")))
        self.assertEqual(self.read("UDC"), "fake.udc")
        self.assertTrue(os.path.exists(self.state_file))
        # optional attributes are absent in the fake tree -> warnings, not errors
        self.assertTrue(any("max_speed" in w for w in g.warnings))
        self.assertTrue(any("no_out_endpoint" in w for w in g.warnings))
        self.assertTrue(any("strict_report_types" in w for w in g.warnings))

    def test_absolute_mouse_is_not_boot_protocol(self):
        self.cfg.mouse.mode = "absolute"
        Gadget(self.cfg).up()
        self.assertEqual(self.read("functions", "hid.mouse", "protocol"), "0")
        self.assertEqual(self.read("functions", "hid.mouse", "subclass"), "0")
        self.assertEqual(self.read("functions", "hid.mouse", "report_length"), "6")

    def test_no_strings_directory_when_all_empty(self):
        self.cfg.gadget.manufacturer = self.cfg.gadget.product = ""
        Gadget(self.cfg).up()
        self.assertFalse(os.path.isdir(os.path.join(self.cfg.gadget.configfs, "hidbridge", "strings", "0x409")))

    def test_down_unbinds_and_unlinks(self):
        g = Gadget(self.cfg)
        g.up()
        root = os.path.join(self.cfg.gadget.configfs, "hidbridge")
        g.down()
        self.assertEqual(self.read("UDC"), "")
        self.assertFalse(os.path.lexists(os.path.join(root, "configs", "c.1", "hid.kbd")))
        self.assertFalse(os.path.lexists(os.path.join(root, "configs", "c.1", "hid.mouse")))
        self.assertFalse(os.path.exists(self.state_file))

    def test_up_is_idempotent_when_bound(self):
        g = Gadget(self.cfg)
        g.up()
        with mock.patch.object(gadget_module, "_write") as write:
            g.up()
            write.assert_not_called()

    def test_no_udc_is_a_clear_error(self):
        with mock.patch.object(gadget_module, "list_udcs", return_value=[]):
            with self.assertRaises(GadgetError) as ctx:
                Gadget(self.cfg).pick_udc(timeout=0)
        self.assertIn("dtoverlay=dwc2", str(ctx.exception))

    def test_status_reports_tree(self):
        g = Gadget(self.cfg)
        self.assertFalse(g.status()["exists"])
        g.up()
        with mock.patch.object(gadget_module, "udc_state", return_value={"udc": "fake.udc", "state": "configured",
                                                                            "current_speed": "full-speed",
                                                                            "maximum_speed": "full-speed", "function": ""}):
            st = g.status()
        self.assertTrue(st["bound"])
        self.assertEqual(st["descriptor"]["idVendor"], "0x1209")
        self.assertEqual(st["functions"]["keyboard"]["protocol"], "1")
        self.assertEqual(st["udc"]["state"], "configured")


if __name__ == "__main__":
    unittest.main()
