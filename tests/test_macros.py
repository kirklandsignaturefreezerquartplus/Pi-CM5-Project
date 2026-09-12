import unittest

from hid_bridge.macros import MacroEngine, MacroError, parse_combo, parse_step


class FakeTarget:
    def __init__(self):
        self.key_events = []
        self.moves = []
        self.button_events = []
        self.abs = []

    def macro_keys_changed(self):
        self.key_events.append(set(self.engine.pressed))

    def macro_mouse_move(self, dx, dy, wheel):
        self.moves.append((dx, dy, wheel))

    def macro_mouse_to(self, x, y):
        self.abs.append((x, y))

    def macro_buttons_changed(self):
        self.button_events.append(self.engine.buttons)


def drain(engine, target, limit=10_000):
    now = 0.0
    steps = 0
    while engine.next_deadline() is not None:
        now = engine.next_deadline()
        engine.run_due(now)
        steps += 1
        if steps > limit:
            raise AssertionError("macro did not finish")
    return now


class ParseTests(unittest.TestCase):
    def test_combo(self):
        self.assertEqual(parse_combo("ctrl+alt+delete"), (0xE0, 0xE2, 0x4C))
        self.assertEqual(parse_combo("Win+L"), (0xE3, 0x0F))
        self.assertEqual(parse_combo("ctrl++"), (0xE0, 0x2E))
        self.assertEqual(parse_combo("+"), (0x2E,))
        with self.assertRaises(MacroError):
            parse_combo("ctrl+bogus")
        with self.assertRaises(MacroError):
            parse_combo("")

    def test_steps(self):
        self.assertEqual(parse_step("ctrl+alt+delete").kind, "tap")
        self.assertEqual(parse_step("tap enter").keys, (0x28,))
        self.assertEqual(parse_step("press shift").kind, "press")
        self.assertEqual(parse_step("release shift").kind, "release")
        self.assertEqual(parse_step("release all").kind, "release_all")
        s = parse_step("type Hello,  world!")
        self.assertEqual((s.kind, s.text), ("type", "Hello,  world!"))
        self.assertEqual(parse_step("TYPE x").text, "x")
        self.assertEqual(parse_step("wait 250").ms, 250)
        s = parse_step("mouse move -10 25")
        self.assertEqual((s.kind, s.dx, s.dy), ("mouse_move", -10, 25))
        s = parse_step("mouse click right 2")
        self.assertEqual((s.kind, s.button, s.count), ("mouse_click", 1, 2))
        self.assertEqual(parse_step("mouse wheel -3").dy, -3)
        self.assertEqual(parse_step("mouse to 100 200").kind, "mouse_to")
        self.assertEqual(parse_step("mouse down left").kind, "mouse_down")
        self.assertEqual(parse_step("mouse up middle").button, 2)
        self.assertEqual(parse_step("macro foo", {"foo": []}).name, "foo")

    def test_step_errors(self):
        for bad in ("", "wait", "wait -1", "wait abc", "press", "mouse", "mouse click", "mouse click nope",
                    "mouse move 1", "macro", "tap", "release"):
            with self.assertRaises(MacroError, msg=bad):
                parse_step(bad)
        with self.assertRaises(MacroError):
            parse_step("macro missing", {"other": []})


class EngineTests(unittest.TestCase):
    def make(self, macros, tap_ms=30, step_ms=20):
        target = FakeTarget()
        engine = MacroEngine(target, macros, tap_ms=tap_ms, step_ms=step_ms)
        target.engine = engine
        return engine, target

    def test_tap_sequence(self):
        engine, target = self.make({"cad": ["ctrl+alt+delete"]})
        engine.start("cad")
        drain(engine, target)
        self.assertEqual(target.key_events, [{0xE0, 0xE2, 0x4C}, set()])
        self.assertEqual(engine.stats()["completed"], 1)
        self.assertEqual(engine.running, 0)

    def test_type_shift_handling(self):
        engine, target = self.make({"t": ["type aB!"]})
        engine.start("t")
        drain(engine, target)
        presses = [ev for ev in target.key_events if ev]
        self.assertEqual(presses, [{0x04}, {0xE1, 0x05}, {0xE1, 0x1E}])

    def test_timing(self):
        engine, target = self.make({"m": ["a", "wait 500", "b"]}, tap_ms=30, step_ms=20)
        engine.start("m", now=0.0)
        end = drain(engine, target)
        # a: 30 + 20, wait 500, b: 30 + 20
        self.assertAlmostEqual(end, 0.6, places=6)

    def test_jitter_bounds(self):
        target = FakeTarget()
        engine = MacroEngine(target, {"m": ["type ab", "wait 0"]}, tap_ms=30, step_ms=20, jitter_ms=40)
        target.engine = engine
        engine.start("m", now=0.0)
        end = drain(engine, target)
        # 2 taps + 2 gaps = 100 ms minimum, plus at most 4 * 40 ms jitter
        self.assertGreaterEqual(end, 0.1)
        self.assertLessEqual(end, 0.1 + 0.16 + 1e-9)
        self.assertEqual(engine.tap_delay() if engine.jitter_ms == 0 else 0.03, 0.03)

    def test_nested_and_depth_limit(self):
        engine, target = self.make({"outer": ["macro inner", "b"], "inner": ["a"], "loop": ["macro loop"]})
        engine.start("outer")
        drain(engine, target)
        presses = [ev for ev in target.key_events if ev]
        self.assertEqual(presses, [{0x04}, {0x05}])
        engine.start("loop")
        drain(engine, target)
        self.assertEqual(engine.stats()["failed"], 1)
        self.assertEqual(engine.pressed, set())

    def test_mouse_steps(self):
        engine, target = self.make({"m": ["mouse move 5 -5", "mouse click left 2", "mouse wheel 3", "mouse down right", "release all"]})
        engine.start("m")
        drain(engine, target)
        self.assertEqual(target.moves, [(5, -5, 0), (0, 0, 3)])
        self.assertEqual(target.button_events, [1, 0, 1, 0, 2, 0])

    def test_unknown_macro(self):
        engine, _ = self.make({})
        with self.assertRaises(MacroError):
            engine.start("nope")

    def test_concurrent_macros_interleave(self):
        engine, target = self.make({"a": ["press ctrl", "wait 100", "release ctrl"], "b": ["x"]})
        engine.start("a")
        engine.run_due(0.0)
        engine.start("b")
        drain(engine, target)
        # ctrl stays held while x is tapped
        self.assertIn({0xE0, 0x1B}, target.key_events)
        self.assertEqual(engine.pressed, set())


if __name__ == "__main__":
    unittest.main()
