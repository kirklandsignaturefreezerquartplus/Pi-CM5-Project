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
| `ctrl+alt+delete`, `tap <combo>` | modifiers go down first; after `tap_ms/2` the other keys go down, are held `tap_ms`, released, and the modifiers come up `tap_ms/2` later (combos with only modifiers or only plain keys go down and up as one report) |
| `press <combo>` / `release <combo>` | hold keys across later steps / release them |
| `release all` | release all keys and mouse buttons held by macros |
| `type <text>` | type the rest of the line using the US layout (`\n` in TOML strings is Enter, `\t` Tab); shifted characters use the same modifier lead as taps; a character the US layout cannot produce is skipped with a journal warning |
| `wait <ms>` | pause; pass-through input keeps flowing meanwhile |
| `mouse move <dx> <dy>` | relative motion, delivered ±127 per host poll; at most ±4095 can be pending at once. In `absolute` mode it moves the virtual cursor by dx × `rel_to_abs_gain` |
| `mouse to <x> <y>` | absolute position 0..32767 (needs `mouse.mode = "absolute"`; otherwise ignored with a journal warning) |
| `mouse click <btn> [n]` | click `left`/`right`/`middle` n times; `back`/`forward` (also `side`/`extra`/`1`–`5`) need `mouse.buttons = 5` and are dropped with 3 buttons |
| `mouse down <btn>` / `mouse up <btn>` | hold / release a button |
| `mouse wheel <n>` | scroll; positive = away from you |
| `macro <name>` | run another macro inline (depth ≤ 8; recursion aborts the macro, releases every macro-held key and button and counts in `macros.failed`) |

Key names in combos: `ctrl shift alt win` (and `rctrl rshift ralt rwin`),
`enter esc tab space backspace delete insert home end pageup pagedown up down
left right`, `f1`–`f24`, `a`–`z`, `0`–`9`, punctuation names (`minus equal
leftbrace rightbrace backslash semicolon apostrophe grave comma period
slash`), keypad `kp0`–`kp9 kpenter kpplus …`, `capslock numlock scrolllock
printscreen pause menu`, any evdev name such as `KEY_F13`, or a raw usage
like `0x68`.  `hid-bridge check` rejects unknown key names in steps and
bindings, and bindings that name a missing macro.  Keys above usage 0x65
(F13–F24, mute and volume, most raw usages) are only delivered with
`keyboard.descriptor = "extended"`; with the default `boot` descriptor they
are silently dropped.  More than six non-modifier keys held at once (sources
and macros combined) sends the HID ErrorRollOver report, as a keyboard does.

Timing: `bridge.tap_ms` (default 30) is the hold time for taps and typed
characters, `bridge.step_ms` (default 20) the gap after every step, typed
character and repeated click (not after `wait`).  `bridge.macro_jitter_ms`
(default 30) adds 0..N ms of right-skewed random jitter (triangular, mode at
about a third of N) to every hold, gap and modifier lead, so with the
defaults a tap is held 30–60 ms; set it to 0 for exact timing.  Some UEFI
setup screens and login prompts want slower input; add `wait` steps or raise
`tap_ms`.

Macro key presses are merged with pass-through keys: holding Shift on the
PiKVM while a macro taps `a` yields a capital A on the PC.  Macros run
concurrently and cooperatively.  Macro-held keys live in one shared set: a
release by any macro releases the key even if another macro pressed it too.

## Macro devices

Any keyboard-like device plugged into the CM5 can drive macros instead of
being forwarded:

```toml
[[inputs]]
label   = "12-key macro pad"
vendor  = 0x1a2c          # from `hid-bridge inputs`
product = 0x2d43
role    = "macro"
unbound = "drop"          # keys without a binding: drop | passthrough (drop also discards
                          # the device's mouse motion and unbound buttons)
[inputs.bindings]
KEY_1 = "ctrl_alt_del"
KEY_2 = "lock"
KEY_KP0 = "autopilot_on"
BTN_LEFT = "login"        # a spare mouse works too
```

Rules are matched top to bottom on any subset of `name` (regex), `phys`
(regex on the USB port path), `vendor`, `product`.  A rule may also carry
`label` (free text shown in logs and status) and `grab = true|false` to
override `bridge.grab_inputs` for that device.  Bound keys never reach the
PC in either `unbound` mode.  Two identical keypads are
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

Commands: `status`, `inputs`, `macro {name}`, `steps {steps:[...]}` (a
non-empty list), `type {text}`, `keys {combo}` (any single step string is
accepted), `release_all`.  Replies: `macro` → `{"started": name}`, `steps` →
`{"started": [step descriptions]}`, `type` → `{"typing": <characters>}`,
`keys` → `{"started": description}`, `release_all` → `{"released": true}`;
the macro then runs asynchronously.  Send the request immediately after
connecting (the server waits at most 50 ms), at most 64 KiB, newline
terminated; the reply is one newline-terminated line.  Every reply is
`{"ok": true, "result": ...}` or `{"ok": false, "error": "..."}`.

Because the socket is local to the CM5, anything that can reach it (SSH,
cron, a home-automation agent) can inject input into the PC.  Keep the CM5's
network administration surface locked down accordingly.
