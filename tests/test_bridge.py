"""End-to-end bridge behaviour with fake evdev sources and fake hidg sinks."""
import os
import unittest

from hid_bridge import linux_input as li
from hid_bridge.bridge import Bridge, Source
from hid_bridge.config import InputRule, parse_config
from hid_bridge.keymap import KEY_CODES


class FakeHidg:
    def __init__(self, report_length):
        self.report_length = report_length
        self.reports = []
        self.last_report = None
        self.fd = -1
        self.path = "<fake>"

        self.get_reports = []
        self.host_disabled = False
        self.disconnected = False
        self.writable = True   # False = previous report still waiting for the host to poll

    def write_report(self, report, force=False, get_report=None):
        assert len(report) == self.report_length
        cache = report if get_report is None else get_report
        if not self.get_reports or self.get_reports[-1] != cache:
            self.get_reports.append(bytes(cache))
        if not force and report == self.last_report:
            return True
        if not self.writable or self.disconnected:
            return False
        self.reports.append(bytes(report))
        self.last_report = bytes(report)
        return True

    def read_output_report(self):
        return None

    @property
    def poll_readable(self):
        return not self.host_disabled

    def host_state_changed(self, state):
        if state == "configured":
            self.host_disabled = False

    def stats(self):
        return {"sent": len(self.reports), "dropped": 0, "host_connected": True, "device": self.path}

    def open(self):
        pass

    def close(self):
        pass


class FakeIdentity:
    def __init__(self, name="Fake", vendor=0x1234, product=0x5678):
        self.name, self.phys, self.uniq = name, "usb-fake/input0", ""
        self.bustype, self.vendor, self.product, self.version = 3, vendor, product, 0x111


class FakeDevice:
    _next_fd = 1000

    def __init__(self, name="Fake", keyboard=True, mouse=False, absolute=False, leds=True):
        FakeDevice._next_fd += 1
        self.fd = FakeDevice._next_fd
        self.path = f"/dev/input/fake{self.fd}"
        self.identity = FakeIdentity(name)
        self.is_keyboard = keyboard
        self.is_mouse = mouse
        self.has_abs_pointer = absolute
        self.absinfo = {li.ABS_X: li.AbsInfo(0, 0, 32767, 0, 0, 0), li.ABS_Y: li.AbsInfo(0, 0, 32767, 0, 0, 0)} if absolute else {}
        self.led_bits = {li.LED_NUML, li.LED_CAPSL, li.LED_SCROLLL} if leds else set()
        self.leds = {}
        self.grabbed = True
        self.queue = []
        self.closed = False
        self.name = name

    def read_events(self):
        if self.queue is None:
            raise OSError(19, "No such device")
        events, self.queue = self.queue, []
        return events

    def set_led(self, code, on):
        if code in self.led_bits:
            self.leds[code] = on

    def close(self):
        self.closed = True


def make_bridge(mouse_mode="relative", buttons=3, descriptor="boot", macros=None):
    cfg = parse_config({
        "keyboard": {"descriptor": descriptor},
        "mouse": {"mode": mouse_mode, "buttons": buttons},
        "bridge": {"control_socket": ""},
        "macros": macros or {},
    })
    bridge = Bridge(cfg, {"keyboard": "/dev/null", "mouse": "/dev/null"})
    bridge.kbd = FakeHidg(8)
    bridge.kbd.last_report = bytes(8)  # run() sends the idle report at start-up
    bridge.mouse = FakeHidg(4 if mouse_mode == "relative" else 6)
    return bridge


def attach(bridge, dev, rule=None):
    src = Source(dev, rule or InputRule(label="test"))
    bridge.sources[dev.fd] = src
    bridge.by_path[dev.path] = src
    return src


def key(code_name, value):
    return (li.EV_KEY, KEY_CODES[code_name], value)


SYN = (li.EV_SYN, li.SYN_REPORT, 0)


class KeyboardPassthroughTests(unittest.TestCase):
    def tearDown(self):
        pass

    def test_key_press_release(self):
        bridge = make_bridge()
        dev = FakeDevice()
        src = attach(bridge, dev)
        dev.queue = [key("KEY_LEFTCTRL", 1), SYN, key("KEY_C", 1), SYN, key("KEY_C", 0), SYN, key("KEY_LEFTCTRL", 0), SYN]
        bridge._process(src)
        self.assertEqual(bridge.kbd.reports, [
            bytes([0x01, 0, 0, 0, 0, 0, 0, 0]),
            bytes([0x01, 0, 0x06, 0, 0, 0, 0, 0]),
            bytes([0x01, 0, 0, 0, 0, 0, 0, 0]),
            bytes(8),
        ])

    def test_autorepeat_ignored_and_unknown_keys_skipped(self):
        bridge = make_bridge()
        dev = FakeDevice()
        src = attach(bridge, dev)
        dev.queue = [key("KEY_A", 1), SYN, key("KEY_A", 2), SYN, key("KEY_A", 2), SYN, key("KEY_WLAN", 1), SYN]
        bridge._process(src)
        self.assertEqual(bridge.kbd.reports, [bytes([0, 0, 0x04, 0, 0, 0, 0, 0])])

    def test_two_sources_merge(self):
        bridge = make_bridge()
        a = attach(bridge, FakeDevice("A"))
        b = attach(bridge, FakeDevice("B"))
        a.dev.queue = [key("KEY_LEFTSHIFT", 1), SYN]
        bridge._process(a)
        b.dev.queue = [key("KEY_B", 1), SYN]
        bridge._process(b)
        self.assertEqual(bridge.kbd.reports[-1], bytes([0x02, 0, 0x05, 0, 0, 0, 0, 0]))
        # unplugging A releases shift but leaves B's key
        a.dev.queue = None
        bridge._process(a)
        self.assertEqual(bridge.kbd.reports[-1], bytes([0x00, 0, 0x05, 0, 0, 0, 0, 0]))
        self.assertTrue(a.dev.closed)
        self.assertNotIn(a.dev.fd, bridge.sources)

    def test_boot_descriptor_drops_f13(self):
        bridge = make_bridge(descriptor="boot")
        src = attach(bridge, FakeDevice())
        src.dev.queue = [key("KEY_F13", 1), SYN]
        bridge._process(src)
        self.assertEqual(bridge.kbd.reports, [])  # identical to idle -> suppressed
        bridge = make_bridge(descriptor="extended")
        src = attach(bridge, FakeDevice())
        src.dev.queue = [key("KEY_F13", 1), SYN]
        bridge._process(src)
        self.assertEqual(bridge.kbd.reports[-1][2], 0x68)

    def test_non_led_set_report_ignored(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice())
        bridge.kbd.read_output_report = lambda: bytes(8)  # a SET_REPORT(Input) sneaking through
        bridge._handle_leds()
        self.assertEqual(src.dev.leds, {})
        bridge.kbd.read_output_report = lambda: bytes([0b100])
        bridge._handle_leds()
        self.assertTrue(src.dev.leds[li.LED_SCROLLL])

    def test_leds_forwarded(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice())
        bridge.kbd.read_output_report = lambda: bytes([0b011])  # num + caps
        bridge._handle_leds()
        self.assertEqual(src.dev.leds, {li.LED_NUML: True, li.LED_CAPSL: True, li.LED_SCROLLL: False})
        # a newly attached keyboard gets the current LED state
        late = attach(bridge, FakeDevice("late"))
        bridge._apply_leds(late)
        self.assertTrue(late.dev.leds[li.LED_CAPSL])


class MousePassthroughTests(unittest.TestCase):
    def test_relative_motion_and_buttons(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        src.dev.queue = [(li.EV_REL, li.REL_X, 5), (li.EV_REL, li.REL_Y, -2), SYN,
                         (li.EV_KEY, li.BTN_LEFT, 1), SYN, (li.EV_REL, li.REL_WHEEL, 1), SYN,
                         (li.EV_KEY, li.BTN_LEFT, 0), SYN]
        bridge._process(src)
        self.assertEqual(bridge.mouse.reports, [
            bytes([0, 5, 0xFE, 0]),
            bytes([1, 0, 0, 0]),
            bytes([1, 0, 0, 1]),
            bytes([0, 0, 0, 0]),
        ])

    def test_get_report_cache_has_no_motion(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        src.dev.queue = [(li.EV_KEY, li.BTN_LEFT, 1), (li.EV_REL, li.REL_X, 40), SYN]
        bridge._process(src)
        self.assertEqual(bridge.mouse.reports, [bytes([1, 40, 0, 0])])
        self.assertEqual(bridge.mouse.get_reports[-1], bytes([1, 0, 0, 0]))
        bridge = make_bridge(mouse_mode="absolute")
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        src.dev.queue = [(li.EV_REL, li.REL_WHEEL, -1), SYN]
        bridge._process(src)
        self.assertEqual(bridge.mouse.reports[-1][5], 0xFF)
        self.assertEqual(bridge.mouse.get_reports[-1][5], 0)

    def test_hwheel_and_hires_ignored(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        src.dev.queue = [(li.EV_REL, li.REL_HWHEEL, 1), (li.EV_REL, li.REL_WHEEL_HI_RES, 120), SYN]
        bridge._process(src)
        self.assertEqual(bridge.mouse.reports, [])

    def test_large_motion_split(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        src.dev.queue = [(li.EV_REL, li.REL_X, 400), SYN]
        bridge._process(src)
        self.assertEqual(len(bridge.mouse.reports), 4)
        self.assertEqual(sum(int.from_bytes(r[1:2], "little", signed=True) for r in bridge.mouse.reports), 400)

    def test_absolute_source_to_relative_output(self):
        bridge = make_bridge(mouse_mode="relative")
        src = attach(bridge, FakeDevice("Tablet", keyboard=False, mouse=True, absolute=True))
        src.dev.queue = [(li.EV_ABS, li.ABS_X, 0), (li.EV_ABS, li.ABS_Y, 0), SYN,
                         (li.EV_ABS, li.ABS_X, 32767), (li.EV_ABS, li.ABS_Y, 32767), SYN]
        bridge._process(src)
        # first position only sets the anchor (zero-motion report), second moves full screen
        total_x = sum(int.from_bytes(r[1:2], "little", signed=True) for r in bridge.mouse.reports)
        total_y = sum(int.from_bytes(r[2:3], "little", signed=True) for r in bridge.mouse.reports)
        self.assertEqual((total_x, total_y), (1919, 1079))

    def test_absolute_source_to_absolute_output(self):
        bridge = make_bridge(mouse_mode="absolute")
        src = attach(bridge, FakeDevice("Tablet", keyboard=False, mouse=True, absolute=True))
        src.dev.queue = [(li.EV_ABS, li.ABS_X, 16383), (li.EV_ABS, li.ABS_Y, 0), SYN, (li.EV_KEY, li.BTN_RIGHT, 1), SYN]
        bridge._process(src)
        self.assertEqual(bridge.mouse.reports[0], bytes([0, 0xFF, 0x3F, 0, 0, 0]))
        self.assertEqual(bridge.mouse.reports[1], bytes([2, 0xFF, 0x3F, 0, 0, 0]))

    def test_relative_source_to_absolute_output(self):
        bridge = make_bridge(mouse_mode="absolute")
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        src.dev.queue = [(li.EV_REL, li.REL_X, 10), SYN]
        bridge._process(src)
        x = int.from_bytes(bridge.mouse.reports[-1][1:3], "little")
        self.assertEqual(x, 0x7FFF // 2 + 170)

    def test_five_button_mask(self):
        bridge = make_bridge(buttons=5)
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        src.dev.queue = [(li.EV_KEY, li.BTN_SIDE, 1), (li.EV_KEY, li.BTN_EXTRA, 1), SYN]
        bridge._process(src)
        self.assertEqual(bridge.mouse.reports[-1][0], 0b11000)
        bridge3 = make_bridge(buttons=3)
        src3 = attach(bridge3, FakeDevice("M", keyboard=False, mouse=True))
        src3.dev.queue = [(li.EV_KEY, li.BTN_SIDE, 1), SYN]
        bridge3._process(src3)
        self.assertEqual(bridge3.mouse.reports[-1][0], 0)


class MacroDeviceTests(unittest.TestCase):
    def test_bound_key_runs_macro_and_unbound_dropped(self):
        bridge = make_bridge(macros={"cad": ["ctrl+alt+delete"]})
        rule = InputRule(role="macro", bindings={"KEY_1": "cad"}, unbound="drop")
        src = attach(bridge, FakeDevice("Pad"), rule)
        src.dev.queue = [key("KEY_1", 1), SYN, key("KEY_1", 0), SYN, key("KEY_2", 1), SYN]
        bridge._process(src)
        self.assertEqual(bridge.kbd.reports, [bytes([0x05, 0, 0x4C, 0, 0, 0, 0, 0])])
        while bridge.macro.next_deadline() is not None:
            bridge.macro.run_due(bridge.macro.next_deadline())
        self.assertEqual(bridge.kbd.reports[-1], bytes(8))
        self.assertEqual(bridge.macro.stats()["completed"], 1)

    def test_unbound_passthrough(self):
        bridge = make_bridge(macros={"cad": ["ctrl+alt+delete"]})
        rule = InputRule(role="macro", bindings={"KEY_1": "cad"}, unbound="passthrough")
        src = attach(bridge, FakeDevice("Pad"), rule)
        src.dev.queue = [key("KEY_2", 1), SYN]
        bridge._process(src)
        self.assertEqual(bridge.kbd.reports[-1][2], 0x1F)

    def test_macro_keys_merge_with_passthrough(self):
        bridge = make_bridge(macros={"hold": ["press ctrl", "wait 100", "release ctrl"]})
        src = attach(bridge, FakeDevice("K"))
        bridge.macro.start("hold")
        bridge.macro.run_due(0)
        src.dev.queue = [key("KEY_C", 1), SYN, key("KEY_C", 0), SYN]
        bridge._process(src)
        self.assertIn(bytes([0x01, 0, 0x06, 0, 0, 0, 0, 0]), bridge.kbd.reports)

    def test_control_commands(self):
        bridge = make_bridge(macros={"cad": ["ctrl+alt+delete"]})
        self.assertEqual(bridge.handle_control({"cmd": "macro", "name": "cad"}), {"started": "cad"})
        self.assertEqual(bridge.handle_control({"cmd": "type", "text": "hi"}), {"typing": 2})
        self.assertIn("started", bridge.handle_control({"cmd": "keys", "combo": "win+l"}))
        self.assertIn("started", bridge.handle_control({"cmd": "steps", "steps": ["a", "wait 1"]}))
        with self.assertRaises(ValueError):
            bridge.handle_control({"cmd": "steps", "steps": []})
        with self.assertRaises(ValueError):
            bridge.handle_control({"cmd": "nope"})
        status = bridge.handle_control({"cmd": "status"})
        self.assertEqual(status["macros"]["running"], 4)
        self.assertEqual(bridge.handle_control({"cmd": "release_all"}), {"released": True})
        self.assertEqual(bridge.kbd.last_report, bytes(8))


class HostBackpressureTests(unittest.TestCase):
    """The host stops polling for a while: latest state must win, nothing may stick."""

    def test_key_released_during_stall_is_not_stuck(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice())
        src.dev.queue = [key("KEY_A", 1), SYN]
        bridge._process(src)
        self.assertEqual(bridge.kbd.reports[-1][2], 0x04)
        bridge.kbd.writable = False                 # host busy / suspended
        src.dev.queue = [key("KEY_A", 0), SYN, key("KEY_B", 1), SYN, key("KEY_B", 0), SYN]
        bridge._process(src)
        self.assertEqual(len(bridge.kbd.reports), 1)  # nothing could go out
        self.assertTrue(bridge._kbd_dirty)
        bridge.kbd.writable = True                  # host polls again
        bridge._pump_keyboard()
        self.assertEqual(bridge.kbd.reports[-1], bytes(8))   # current state, not a stale key-down
        self.assertFalse(bridge._kbd_dirty)

    def test_motion_accumulates_between_polls(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        bridge.mouse.writable = False
        for dx in (5, 7, -2):
            src.dev.queue = [(li.EV_REL, li.REL_X, dx), (li.EV_REL, li.REL_WHEEL, 1), SYN]
            bridge._process(src)
        self.assertEqual(bridge.mouse.reports, [])
        bridge.mouse.writable = True
        bridge._pump_mouse()
        self.assertEqual(bridge.mouse.reports, [bytes([0, 10, 0, 3])])   # one report, summed like a real mouse
        self.assertFalse(bridge._mouse_dirty)

    def test_button_press_and_release_during_stall(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        bridge.mouse.writable = False
        src.dev.queue = [(li.EV_KEY, li.BTN_LEFT, 1), SYN, (li.EV_KEY, li.BTN_LEFT, 0), SYN]
        bridge._process(src)
        bridge.mouse.writable = True
        bridge._pump_mouse()
        # buttons ended where they started and there was no motion: nothing to send
        self.assertEqual(bridge.mouse.reports, [])
        self.assertFalse(bridge._mouse_dirty)

    def test_no_duplicate_idle_mouse_reports(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        src.dev.queue = [(li.EV_REL, li.REL_X, 3), SYN]
        bridge._process(src)
        bridge._emit_mouse_motion(0, 0, 0)
        bridge._emit_mouse_motion(0, 0, 0)
        self.assertEqual(bridge.mouse.reports, [bytes([0, 3, 0, 0])])

    def test_motion_discarded_while_host_away_buttons_kept(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        bridge.mouse.disconnected = True
        src.dev.queue = [(li.EV_REL, li.REL_X, 50), (li.EV_KEY, li.BTN_RIGHT, 1), SYN]
        bridge._process(src)
        self.assertEqual((bridge._mouse_dx, bridge._mouse_dy), (0, 0))
        self.assertTrue(bridge._mouse_dirty)
        bridge.mouse.disconnected = False
        bridge._pump_mouse()
        self.assertEqual(bridge.mouse.reports, [bytes([2, 0, 0, 0])])

    def test_resync_after_host_returns(self):
        bridge = make_bridge()
        bridge.udc = "fake"
        src = attach(bridge, FakeDevice())
        src.dev.queue = [key("KEY_LEFTSHIFT", 1), SYN]
        bridge._process(src)
        bridge.kbd.host_disabled = True
        bridge.kbd.last_report = None
        import hid_bridge.bridge as bridge_module
        original = bridge_module.udc_current_state
        bridge_module.udc_current_state = lambda udc: "configured"
        try:
            bridge._poll_host_state()
        finally:
            bridge_module.udc_current_state = original
        self.assertEqual(bridge.kbd.reports[-1][0], 0x02)   # shift still held: host told again


class ShutdownTests(unittest.TestCase):
    def test_shutdown_releases_everything(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("K", keyboard=True, mouse=True))
        src.dev.queue = [key("KEY_A", 1), (li.EV_KEY, li.BTN_LEFT, 1), SYN]
        bridge._process(src)
        bridge.shutdown()
        self.assertEqual(bridge.kbd.reports[-1], bytes(8))
        self.assertEqual(bridge.mouse.reports[-1], bytes(4))
        self.assertTrue(src.dev.closed)
        self.assertEqual(bridge.sources, {})


if __name__ == "__main__":
    unittest.main()
