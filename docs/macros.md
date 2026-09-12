# Macros, macro devices and the control socket

## Step language

A macro is a named list of step strings in `[macros]`:

```toml
[macros]
ctrl_alt_del = ["ctrl+alt+delete"]
lock         = ["win+l"]
login        = ["ctrl+alt+delete", "wait 1200", "type hunter2", "enter"]
autopilot_on = ["press shift", "tap a", "release shift", "wait 50", "mouse click left"]
```

| Step | Meaning |
|---|---|
| `ctrl+alt+delete`, `tap <combo>` | press every key in the combo, hold `bridge.tap_ms`, release |
| `press <combo>` / `release <combo>` | hold keys across later steps / release them |
| `release all` | release all keys and mouse buttons held by macros |
| `type <text>` | type the rest of the line using the US layout (`\n` in TOML strings is Enter) |
| `wait <ms>` | pause; pass-through input keeps flowing meanwhile |
| `mouse move <dx> <dy>` | relative motion (any size; split into ±127 reports) |
| `mouse to <x> <y>` | absolute position 0..32767 (needs `mouse.mode = "absolute"`) |
| `mouse click <btn> [n]` | click `left`/`right`/`middle`/`back`/`forward` n times |
| `mouse down <btn>` / `mouse up <btn>` | hold / release a button |
| `mouse wheel <n>` | scroll; positive = away from you |
| `macro <name>` | run another macro inline (depth ≤ 8, recursion aborts) |

Key names in combos: `ctrl shift alt win` (and `rctrl rshift ralt rwin`),
`enter esc tab space backspace delete insert home end pageup pagedown up down
left right`, `f1`–`f24`, `a`–`z`, `0`–`9`, punctuation names (`minus equal
leftbrace rightbrace backslash semicolon apostrophe grave comma period
slash`), keypad `kp0`–`kp9 kpenter kpplus …`, `capslock numlock scrolllock
printscreen pause menu`, any evdev name such as `KEY_F13`, or a raw usage
like `0x68`.  `hid-bridge check` fails at start-up on any typo.

Timing: `bridge.tap_ms` (default 30) is the hold time for taps and typed
characters, `bridge.step_ms` (default 20) the gap between steps.  Some UEFI
setup screens and login prompts want slower input; add `wait` steps or raise
`tap_ms`.

Macro key presses are merged with pass-through keys: holding Shift on the
PiKVM while a macro taps `a` yields a capital A on the PC.  Macros run
concurrently and cooperatively; two macros pressing the same key release it
when the last one releases.

## Macro devices

Any keyboard-like device plugged into the CM5 can drive macros instead of
being forwarded:

```toml
[[inputs]]
label   = "12-key macro pad"
vendor  = 0x1a2c          # from `hid-bridge inputs`
product = 0x2d43
role    = "macro"
unbound = "drop"          # keys without a binding: drop | passthrough
[inputs.bindings]
KEY_1 = "ctrl_alt_del"
KEY_2 = "lock"
KEY_KP0 = "autopilot_on"
BTN_LEFT = "login"        # a spare mouse works too
```

Rules are matched top to bottom on any subset of `name` (regex), `phys`
(regex on the USB port path), `vendor`, `product`.  Two identical keypads are
told apart by `phys`.  Devices with `role = "ignore"` are left alone (use
this for a keyboard you administer the CM5 with).

A macro starts on key **press**; releases are ignored, so holding a pad key
does not repeat the macro.

## Control socket

`hid-bridge` listens on `/run/hid-bridge/ctl.sock` (root, mode 0660).  The CLI
wraps it:

```sh
hid-bridge ctl status                 # bridge, sources, counters, LEDs, macros
hid-bridge ctl inputs                 # attached sources and ignored nodes
hid-bridge ctl macro login
hid-bridge ctl keys ctrl+alt+delete
hid-bridge ctl type "hello world"     # text is joined with spaces
hid-bridge ctl steps "win+r" "wait 400" "type notepad" "enter"
hid-bridge ctl release-all            # panic button: nothing stays pressed
```

Wire protocol: connect, send one JSON object terminated by `\n`, read one JSON
reply.

```sh
printf '{"cmd":"steps","steps":["win+d"]}\n' | socat - UNIX-CONNECT:/run/hid-bridge/ctl.sock
```

```python
import json, socket
s = socket.socket(socket.AF_UNIX); s.connect("/run/hid-bridge/ctl.sock")
s.sendall(json.dumps({"cmd": "macro", "name": "lock"}).encode() + b"\n")
print(json.loads(s.recv(65536)))
```

Commands: `status`, `inputs`, `macro {name}`, `steps {steps:[...]}`,
`type {text}`, `keys {combo}`, `release_all`.  Every reply is
`{"ok": true, "result": ...}` or `{"ok": false, "error": "..."}`.

Because the socket is local to the CM5, anything that can reach it (SSH,
cron, a home-automation agent) can inject input into the PC.  Keep the CM5's
network administration surface locked down accordingly.
