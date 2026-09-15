import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("bundle_tool", os.path.join(ROOT, "tools", "make-review-bundle.py"))
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class BundleToolTests(unittest.TestCase):
    def test_fence_longer_than_any_backtick_run(self):
        self.assertEqual(tool.fence_for("plain"), "```")
        self.assertEqual(tool.fence_for("```python\nx\n```"), "````")
        self.assertEqual(tool.fence_for("`````"), "``````")

    def test_anchor(self):
        self.assertEqual(tool.anchor_for("hid_bridge/bridge.py"), "hid_bridgebridgepy")
        self.assertEqual(tool.anchor_for("docs/usb-identity.md"), "docsusb-identitymd")

    def test_languages(self):
        self.assertEqual(tool.language_for("bin/hid-bridge"), "bash")
        self.assertEqual(tool.language_for("Makefile"), "makefile")
        self.assertEqual(tool.language_for("x/y.patch"), "diff")
        self.assertEqual(tool.language_for("tools/windows/a.ps1"), "powershell")

    def test_round_trip_of_the_real_tree(self):
        bundle = tool.build(ROOT)
        recovered = tool.parse(bundle)
        tracked = tool.tracked_files(ROOT)
        self.assertEqual(set(recovered), set(tracked))
        for path in tracked:
            with open(os.path.join(ROOT, path), "rb") as fh:
                self.assertEqual(recovered[path], fh.read(), path)

    def test_parse_detects_tampering(self):
        bundle = tool.build(ROOT)
        broken = bundle.replace("KEYBOARD_REPORT_LENGTH = 8", "KEYBOARD_REPORT_LENGTH = 9", 1)
        with self.assertRaises(ValueError):
            tool.parse(broken)


if __name__ == "__main__":
    unittest.main()
