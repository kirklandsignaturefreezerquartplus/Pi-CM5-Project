# hid-bridge — CM5 keyboard/mouse device-in-the-middle for PiKVM

A Raspberry Pi Compute Module 5 sits between a PiKVM V4 Plus and the computer
being controlled.  Toward the PC the CM5 is nothing more than a **plain
full-speed USB keyboard and mouse**: one configuration, two boot-protocol HID
interfaces, byte-exact HID-specification report descriptors, no composite
markers, no vendor pages, no Microsoft OS descriptors, no serial number.
Toward the PiKVM (and any local macro keypads) the CM5 is a normal USB host.
Everything received on the host side is normalised and re-transmitted on the
device side as ordinary key and mouse reports.

```
 PiKVM V4 Plus ──USB (OTG out)──► ┌──────────────────────────┐
 macro keypad  ──USB────────────► │  CM5 (USB host ports)    │
 sim panel     ──USB────────────► │   evdev ─► hid-bridge    │
                                  │            │  merge      │
                                  │            ▼             │
                                  │  configfs HID gadget     │ ──USB (device port)──► Target PC
                                  └──────────────────────────┘      "USB Keyboard" + mouse
```

Why a middle box: input multiplexing and macro injection from several local
devices into one virtual keyboard/mouse, guaranteed enumeration in restrictive
pre-boot/UEFI USB stacks that dislike composite KVM gadgets, and isolation of
remote-desktop input from dedicated simulator panels so applications never see
the KVM as a new game controller.

## What the target computer sees

| Field | Value | Set by |
|---|---|---|
| Speed | full-speed (12 Mbit/s) by default, or high-speed | `gadget.max_speed` |
| Device descriptor | USB 2.00, class 0/0/0, EP0 64 bytes | kernel |
| idVendor / idProduct / bcdDevice | 0x1209 / 0x0001 / 1.00 by default, configurable | `gadget.*` |
| Strings | "Generic" / "USB Keyboard" / random serial written at install | `gadget.manufacturer/product/serial` |
| Configuration | 1 config, bus-powered, remote wakeup bit, 100 mA, no OTG descriptor | `gadget.*` |
| Interface 0 | HID class 3, subclass 1 (boot), protocol 1 (keyboard), one interrupt IN endpoint | fixed |
| Report descriptor 0 | 63-byte HID spec Appendix E.6 boot keyboard, byte for byte | `keyboard.descriptor` |
| Interface 1 | HID class 3, subclass 1 (boot), protocol 2 (mouse), one interrupt IN endpoint | `mouse.mode` |
| Report descriptor 1 | boot mouse (buttons, X, Y) + wheel byte | `mouse.buttons` |
| GET_REPORT / SET_PROTOCOL / SET_IDLE / LED SET_REPORT | answered like a real boot keyboard | bridge + kernel |
| MS OS descriptors / WebUSB / report IDs | none | fixed |

`docs/usb-identity.md` is the field-by-field accounting, checked against the
Raspberry Pi 6.12 kernel sources, of what is pinned, what the kernel decides,
what a deep inspection could still notice, and how to verify the enumeration
from Windows or a Linux host.  `kernel-patches/` (five patches for
rpi-6.12.y) removes the remaining kernel-side tells: bcdHID 1.01 and the
Linux interface string, qualifier/LPM answers at full speed, class requests
for report types the device does not have, remote wakeup, and the
self-powered/remote-wakeup/test-mode/interface-status answers of the
standard requests.

**New here?  Read `docs/GUIDE.md`**, the step-by-step implementation, testing,
deployment and use guide written for a first-time builder.  The rest of this
README is the condensed reference.

## Quick start (on the CM5)

Raspberry Pi OS Lite 64-bit (Bookworm or newer, Python ≥ 3.11).  No third-party
packages are needed: the bridge talks to evdev and configfs directly.

```sh
git clone <this repo> && cd Pi-CM5-Project
sudo ./install.sh          # copies to /opt/hid-bridge, installs units, edits config.txt
sudo reboot                # first time only: enables dtoverlay=dwc2,dr_mode=peripheral
```

After the reboot:

```sh
hid-bridge gadget status   # gadget bound, UDC state "configured" once the PC enumerates it
hid-bridge inputs          # what is plugged into the CM5 host ports and how it is treated
hid-bridge ctl status      # live bridge state: sources, reports sent, LEDs, macros
journalctl -u hid-bridge -f
```

Cabling and power are covered in `docs/hardware.md`; PiKVM settings in
`docs/pikvm.md`.

## Configuration

`/etc/hid-bridge/config.toml` (template: `config/config.toml`).  Validate with
`hid-bridge check`, which also prints the exact descriptor bytes the PC will
receive.

* **gadget** — VID/PID, strings, speed, power attributes.
* **keyboard** — `boot` (spec-exact) or `extended` (F13–F24, international keys).
* **mouse** — `relative` (boot-compatible, works in UEFI) or `absolute`
  (PiKVM's tablet-style pointer; needs an OS); 3 or 5 buttons.
* **bridge** — grabbing, hot-plug rescan period, macro timing, LED feedback,
  control socket.
* **inputs** — rules matching devices by name/phys/VID/PID with role
  `passthrough`, `macro` or `ignore`; macro devices bind keys to macros.
* **macros** — named step lists (`docs/macros.md`).

## Macros and scripted input

```sh
hid-bridge ctl macro ctrl_alt_del
hid-bridge ctl keys win+l
hid-bridge ctl type "some text"
hid-bridge ctl steps "ctrl+alt+delete" "wait 1500" "type hunter2" "enter"
hid-bridge ctl release-all
```

The same commands are available to local scripts over the Unix socket
`/run/hid-bridge/ctl.sock` as newline-delimited JSON.  Macro keypads are bound
in `[[inputs]]` rules; their keystrokes never reach the PC directly.

## Behaviour details

* Keyboard state from every source and from running macros is merged into one
  8-byte boot report; more than six keys produces the ErrorRollOver phantom
  state exactly as the HID spec requires.  Autorepeat is left to the host.
* Mouse motion larger than ±127 is split across reports; absolute↔relative
  conversion is available in both directions.
* Caps/Num/Scroll Lock LED state from the PC is written back to every attached
  keyboard, so the PiKVM web UI shows the real lock state.
* Sources are grabbed (`EVIOCGRAB`) so the CM5's own console never acts on
  forwarded keystrokes (Ctrl+Alt+Del included).  Unplugging a source releases
  every key it held.
* The bridge behaves like the device it emulates: one report register per
  interface, key and button transitions are delivered in order, mouse motion
  accumulates between host polls and saturates like an 8-bit counter when
  the host stops collecting.  Nothing blocks and no key can stick.  While
  the PC has suspended the bus the bridge waits with a backoff (motion
  gathered while asleep is discarded, as on a real mouse) and re-sends the
  current state on resume.  A key press wakes a sleeping PC only with
  `kernel-patches/0004`; the descriptor bit is advertised either way, as on
  real keyboards.
* Nothing unsolicited: no report at start-up, and at shutdown only keys or
  buttons that were actually held are released.
* `GET_REPORT(Input)` on the control endpoint is answered instantly with the
  current key/button state, as a real keyboard does, via the kernel's
  GET_REPORT cache.

## Repository layout

```
hid_bridge/          Python package (stdlib only)
  linux_input.py     pure-Python evdev (ioctls, event structs, grab, LEDs)
  keymap.py          evdev ↔ HID usage tables, key aliases, US layout
  descriptors.py     report descriptors + a tiny descriptor parser
  gadget.py          configfs/libcomposite gadget lifecycle
  reports.py         keyboard/mouse report encoding
  bridge.py          main loop: sources, merging, LEDs, control socket
  macros.py          macro language and cooperative scheduler
  control.py         Unix-socket JSON control interface
  __main__.py        CLI: gadget | run | inputs | check | ctl
config/config.toml   annotated default configuration
systemd/             hid-gadget.service (oneshot) and hid-bridge.service
tools/               verify-gadget.sh (CM5), windows/Get-HidBridgeDevices.ps1 (target)
kernel-patches/      optional rpi-6.12.y patches removing kernel-side gadget tells
tools/identity-from-lsusb.py  turn an lsusb -v dump of a reference keyboard into [gadget] settings
docs/                GUIDE (start here), hardware, usb-identity, remaining-tells, review-analysis, pikvm, macros, troubleshooting
tests/               unit tests (python3 -m unittest discover -s tests)
```

## Development

```sh
make test                      # unit tests, no hardware needed
make check                     # validate config/config.toml and dump descriptors
HID_BRIDGE_CONFIG=config/config.toml python3 -m hid_bridge inputs
```

The bridge itself only needs Linux; the gadget half needs a UDC (the CM5's
dwc2 controller in peripheral mode).
