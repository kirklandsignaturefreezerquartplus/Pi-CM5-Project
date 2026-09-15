# hid-bridge: review bundle

Every tracked file of the project in one document, for code review and
portability only.  Nothing runs from this file; install from the
repository.  Regenerate with `tools/make-review-bundle.py` (or `make
bundle`) and verify with `tools/make-review-bundle.py --check`.

* Generated: 2026-09-15 20:06 UTC
* Base commit: `2567d1a` on `claude/eloquent-volta-3036by` (built from the working tree, so the
  content may be ahead of that commit; `--check` compares against the tree)
* Files: 51 (389,231 bytes)

## Contents

1. [README.md](#readmemd)
2. [docs/GUIDE.md](#docsguidemd)
3. [docs/hardware.md](#docshardwaremd)
4. [docs/pikvm.md](#docspikvmmd)
5. [docs/usb-identity.md](#docsusb-identitymd)
6. [docs/remaining-tells.md](#docsremaining-tellsmd)
7. [docs/review-analysis.md](#docsreview-analysismd)
8. [docs/macros.md](#docsmacrosmd)
9. [docs/troubleshooting.md](#docstroubleshootingmd)
10. [config/config.toml](#configconfigtoml)
11. [hid_bridge/__init__.py](#hid_bridge__init__py)
12. [hid_bridge/__main__.py](#hid_bridge__main__py)
13. [hid_bridge/config.py](#hid_bridgeconfigpy)
14. [hid_bridge/descriptors.py](#hid_bridgedescriptorspy)
15. [hid_bridge/keymap.py](#hid_bridgekeymappy)
16. [hid_bridge/reports.py](#hid_bridgereportspy)
17. [hid_bridge/linux_input.py](#hid_bridgelinux_inputpy)
18. [hid_bridge/hidg.py](#hid_bridgehidgpy)
19. [hid_bridge/gadget.py](#hid_bridgegadgetpy)
20. [hid_bridge/macros.py](#hid_bridgemacrospy)
21. [hid_bridge/control.py](#hid_bridgecontrolpy)
22. [hid_bridge/bridge.py](#hid_bridgebridgepy)
23. [tests/__init__.py](#tests__init__py)
24. [tests/test_bridge.py](#teststest_bridgepy)
25. [tests/test_config.py](#teststest_configpy)
26. [tests/test_descriptors.py](#teststest_descriptorspy)
27. [tests/test_gadget.py](#teststest_gadgetpy)
28. [tests/test_hidg.py](#teststest_hidgpy)
29. [tests/test_identity_tool.py](#teststest_identity_toolpy)
30. [tests/test_keymap.py](#teststest_keymappy)
31. [tests/test_linux_input.py](#teststest_linux_inputpy)
32. [tests/test_macros.py](#teststest_macrospy)
33. [tests/test_reports.py](#teststest_reportspy)
34. [tests/test_review_bundle.py](#teststest_review_bundlepy)
35. [tools/identity-from-lsusb.py](#toolsidentity-from-lsusbpy)
36. [tools/make-review-bundle.py](#toolsmake-review-bundlepy)
37. [tools/verify-gadget.sh](#toolsverify-gadgetsh)
38. [tools/windows/Get-HidBridgeDevices.ps1](#toolswindowsget-hidbridgedevicesps1)
39. [bin/hid-bridge](#binhid-bridge)
40. [systemd/hid-bridge.service](#systemdhid-bridgeservice)
41. [systemd/hid-gadget.service](#systemdhid-gadgetservice)
42. [install.sh](#installsh)
43. [uninstall.sh](#uninstallsh)
44. [Makefile](#makefile)
45. [.gitignore](#gitignore)
46. [kernel-patches/README.md](#kernel-patchesreadmemd)
47. [kernel-patches/0001-usb-gadget-f_hid-hid-1.10-idle-0-no-interface-string-no-zlp.patch](#kernel-patches0001-usb-gadget-f_hid-hid-110-idle-0-no-interface-string-no-zlppatch)
48. [kernel-patches/0002-usb-gadget-composite-full-speed-only-when-limited-to-full-speed.patch](#kernel-patches0002-usb-gadget-composite-full-speed-only-when-limited-to-full-speedpatch)
49. [kernel-patches/0003-usb-gadget-f_hid-add-strict_report_types-option.patch](#kernel-patches0003-usb-gadget-f_hid-add-strict_report_types-optionpatch)
50. [kernel-patches/0004-usb-dwc2-gadget-remote-wakeup-f_hid-wakeup_on_write.patch](#kernel-patches0004-usb-dwc2-gadget-remote-wakeup-f_hid-wakeup_on_writepatch)
51. [kernel-patches/0005-usb-dwc2-composite-standard-request-answers-of-a-real-device.patch](#kernel-patches0005-usb-dwc2-composite-standard-request-answers-of-a-real-devicepatch)

## README.md

`9444 bytes, 176 lines, sha256 977b2e3fb6b3d1ca12093e2af7241d57699d5a14f08fc7bd4c739f8bddf9d386`

````markdown
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
rpi-6.12.y) removes the remaining kernel-side tells: bcdHID 1.01, the
Linux interface string, the 4 ms idle rate and the zero-length packet after
every report, qualifier/LPM answers at full speed, class requests
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
* **bridge** — grabbing, hot-plug rescan period, macro timing and jitter,
  LED feedback, control socket, log level.
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
hid-bridge ctl inputs                 # attached sources and ignored devices
```

The same commands are available to local scripts over the Unix socket
`/run/hid-bridge/ctl.sock` as newline-delimited JSON.  Macro keypads are bound
in `[[inputs]]` rules; bound keys never reach the PC, and unbound keys are
dropped unless the rule sets `unbound = "passthrough"`.

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
  GET_REPORT cache (kernel 6.10 or newer; older kernels answer after 2.5 s
  with zeros).

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
tools/make-review-bundle.py   write/verify REVIEW_BUNDLE.md
REVIEW_BUNDLE.md     all of the above in one file for code review and portability; not for use
docs/                GUIDE (start here), hardware, usb-identity, remaining-tells, review-analysis, pikvm, macros, troubleshooting
tests/               unit tests (python3 -m unittest discover -s tests)
```

## Development

```sh
make test                      # unit tests, no hardware needed
make check                     # validate config/config.toml and dump descriptors
make bundle                    # regenerate REVIEW_BUNDLE.md (every tracked file in one document, for review only)
HID_BRIDGE_CONFIG=config/config.toml python3 -m hid_bridge inputs
```

The bridge itself only needs Linux; the gadget half needs a UDC (the CM5's
dwc2 controller in peripheral mode).
````

## docs/GUIDE.md

`38381 bytes, 943 lines, sha256 4bdcffe0f18628536c74c8496fb24c47c3aa2298c357c1eb9b94e8dc2c251748`

````markdown
# hid-bridge: complete implementation, testing, deployment and use guide

This guide takes you from "the CM5 kit boots to a desktop and the PiKVM
already controls my computers through the multiport switch" to a working,
verified bridge that you can operate day to day.  It assumes you are
comfortable typing commands you are given, but have never built a USB gadget,
edited a boot config, or written a systemd service.  Every step says what to
type, what you should see, and what to do if you do not see it.

Time budget: about 2 hours the first time, most of it waiting for downloads
and reboots.  The optional kernel rebuild in Part 9 adds 1 to 2 hours of
mostly unattended time.

---

## Part 0: What you are building

### The idea in one picture

```
                 PiKVM V4 Plus ──HDMI+USB──► PiKVM multiport switch
                                                     │
                                         port N  ────┼──── other ports ──► other computers
                                    HDMI ▲    USB ▼  (unchanged)
                                         │           │
   Target computer ──HDMI out────────────┘           ▼
                                             ┌────────────────────┐
                                             │  CM5 (this guide)  │
   Target computer ◄──USB (looks like a ─────│ USB-C device port  │
                       plain keyboard+mouse) │ USB-A host ports ◄─┼── switch port N USB
                                             │                  ◄─┼── optional macro keypad
                                             └────────────────────┘
```

Today, port N of the switch has two cables to the target computer: HDMI (video
out of the computer) and USB (keyboard and mouse into the computer).  You will
leave the HDMI cable exactly as it is and insert the CM5 into the USB cable:

* The switch's USB cable for port N plugs into one of the CM5's **USB-A** ports
  instead of the computer.  To the switch, the CM5 is a computer.
* A new cable runs from the CM5's **USB-C** port to the computer.  To the
  computer, the CM5 is an ordinary USB keyboard with a built-in mouse.

Software on the CM5 (`hid-bridge`) reads every key press and mouse movement
arriving from the switch and re-sends it out of the USB-C port as standard
keyboard and mouse reports.  Extra devices plugged into the CM5's other USB-A
ports (a macro keypad, a spare mouse) are merged into the same virtual keyboard
and mouse, or bound to macros.

### Words you will meet

| Term | Meaning here |
|---|---|
| **Target / PC** | The computer being controlled.  Windows in this guide, but anything with USB works. |
| **Host port** | A USB port that *accepts* devices.  The CM5 IO Board's two USB-A ports. |
| **Device port / gadget port** | A USB port through which the CM5 *pretends to be a device*.  The CM5 IO Board's USB-C. |
| **Gadget** | Linux's name for a computer acting as a USB device. |
| **HID** | Human Interface Device: the USB class for keyboards and mice. |
| **evdev** | The Linux interface the CM5 uses to read keyboards and mice plugged into its host ports. |
| **Boot protocol** | The simplest keyboard/mouse report format, understood by every BIOS/UEFI. The keyboard always speaks it; the mouse does with `mouse.mode = "relative"` (the default). |
| **Relative / absolute mouse** | A normal mouse sends *movements* (relative). PiKVM by default sends *positions* (absolute), like a drawing tablet. The bridge can output either and converts between them. |
| **PiKVM switch / port N** | The multiport extender attached to the PiKVM, and the port on it whose target gets the CM5. |

---

## Part 1: Before you start

### 1.1 Parts checklist

You already have:

- [ ] PiShop CM5 kit (Compute Module 5 on the official CM5 IO Board, in its
  case, with the kit's 27 W USB-C power supply), booting Raspberry Pi OS.
- [ ] PiKVM V4 Plus and multiport switch, working: you can control the target
  computer through the switch today.
- [ ] The target computer.

You need to add:

- [ ] **A way to power the CM5 that does not use its USB-C connector.**  This
  is the one real hardware wrinkle: on the CM5 IO Board the USB-C connector
  carries *both* the kit's power *and* the USB device data lines.  You cannot
  have the power supply and the target computer plugged into it at the same
  time.  Part 2 walks through the options; the cleanest is the official
  **PoE+ HAT for the CM5 IO Board plus a PoE+ injector or PoE switch port**.
- [ ] **A USB-C power blocker** (sold as "USB-C power blocker", passes data,
  blocks the 5 V line; PortaPow makes one) *or* a cable you are willing to
  modify.  It stops the target computer's 5 V from feeding into the CM5 board.
- [ ] **A USB cable from the CM5's USB-C to the target computer**: USB-C to
  USB-A (or USB-C to USB-C if the target has USB-C).  USB 2.0 rated is fine;
  1 m or shorter.
- [ ] **An adapter or cable so the switch's port-N USB cable fits a USB-A
  socket** on the CM5.  If the switch's downstream cable ends in USB-A you need
  nothing (the CM5 has USB-A sockets); if it ends in USB-C you need a USB-C
  female to USB-A male adapter.
- [ ] Optional: a small USB keypad or spare mouse for macros.
- [ ] Optional, for verification: a plain USB keyboard for the bench test in
  Part 5.

### 1.2 Another computer for administration

Once the bridge runs, **every keyboard and mouse plugged into the CM5 is taken
away from the CM5's own screen and forwarded to the target**.  You therefore
administer the CM5 over the network with SSH from another computer (your
laptop, or the target itself before it is wired in).  Part 3 sets this up.
If you must use a local keyboard on the CM5 later, Part 8.4 shows how to
exclude it.

### 1.3 What could go wrong, and why it will not damage anything

* The bridge only ever sends keyboard and mouse reports.  It cannot install
  anything on the target or read anything from it.
* USB-C power conflicts are the one way to damage hardware.  Part 2 is
  written so that no two power sources are ever connected to the CM5 at once.
* Everything the installer changes is reversible with `uninstall.sh --purge`.

---

## Part 2: Hardware and power

Read this whole part before plugging anything in.

### 2.1 Choose how the CM5 will be powered

The kit powers the CM5 IO Board through its USB-C connector using USB Power
Delivery (5 V, up to 5 A).  That same connector is the only place the CM5's
USB *device* port is available.  You need one of these:

| Option | What you buy | Pros | Cons |
|---|---|---|---|
| **A. PoE+ HAT** (recommended) | Raspberry Pi PoE+ HAT for the CM5 IO Board, plus a PoE+ (802.3at) injector or a PoE+ switch port; a network cable to the IO Board's Ethernet socket | Official, clean, powers the board fully, frees the USB-C completely, gives you wired networking for SSH at the same time | Cost of injector; the HAT sits on the board |
| **B. 5 V into the GPIO header** | A regulated 5 V, 5 A supply with a lead ending in female header pins (or a screw-terminal breakout) | Cheap | Bypasses the board's input protection; wire carefully (5 V to pins 2/4, GND to pin 6); check the CM5 IO Board datasheet for your board revision before using it |
| **C. USB-C "PD + data" Y splitter** | A USB-C splitter that takes a charger on one leg and a data host on the other | No board changes | Many splitters join the two 5 V lines; only use one that explicitly isolates VBUS on the data leg. Least predictable; not recommended |
| **D. Different carrier board** | A CM5 carrier with a separate DC input and a dedicated USB device connector | Purpose-built | You are no longer using the kit's board |

The rest of the guide assumes **A** or **B**.  With either, the USB-C connector
is used only for data to the target computer, through the power blocker.

### 2.2 Why the power blocker

Even with the CM5 powered elsewhere, a normal cable would bring the target
computer's 5 V into the CM5 IO Board's power input.  With two 5 V sources
connected, the board's input circuitry decides which wins, and the target's
port (500 mA) cannot run a CM5.  The power blocker passes the two data wires
and ground but not the 5 V wire, so there is exactly one power source at all
times.  The CM5's USB controller does not need to see the target's 5 V to
work.

If you would rather modify a cable: use a USB-A to USB-C cable, open the
outer jacket in the middle, and cut **only the red wire** (VBUS).  Insulate
both ends.  Mark the cable clearly.

### 2.3 Check the boot strap

On the CM5 IO Board, locate the jumper labelled **nRPIBOOT** (near the USB-C
connector on the official board; check the board's silkscreen).  It must be
**unfitted / open**.  With it fitted, the module ignores its eMMC and presents
itself on the USB-C as a Broadcom programming device; you would have used this
when flashing the module.  Remove it now if it is still in place.

### 2.4 Wiring order

Do these in order; do not skip ahead.

1. **Power down everything**: CM5 (shutdown from the desktop or `sudo
   poweroff`), then unplug its USB-C power supply.
2. **Fit the new power path** (PoE+ HAT and cable, or the 5 V header lead).
   Do not power on yet.
3. **Do not connect the target computer or the switch yet.**  Parts 3 to 5
   install and test the software first with nothing plugged into the USB-C
   port.  The final cabling happens in Part 6.
4. Power the CM5 on through the new path.  Confirm it boots (green activity
   LED, and it appears on the network).

---

## Part 3: Prepare the CM5's operating system

All commands in this part run on the CM5.  Use its screen and keyboard for
3.1, then switch to SSH.

### 3.1 Enable SSH and give the CM5 a name

```sh
sudo raspi-config
```

* *System Options → Hostname*: set `hidbridge` (or any name you like).
* *Interface Options → SSH → Yes*.
* *System Options → Boot / Auto Login*: choose **Console** (not Desktop).
  The bridge does not need a desktop, and a desktop session competes for the
  keyboards you will plug in.
* *Finish*, and reboot when asked.

From your other computer:

```sh
ssh <your-username>@hidbridge.local
```

(Replace `<your-username>` with the account you created when setting up
Raspberry Pi OS.  If `.local` names do not resolve on your network, use the
CM5's IP address from your router.)  Everything from here on is typed in that
SSH session.

### 3.2 Update the system and check prerequisites

```sh
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git
python3 --version
```

Expected: `Python 3.11.x` or newer.  Raspberry Pi OS Bookworm (2023 onwards)
ships 3.11.  If you see 3.9 or older, your OS image is too old; re-image with
the current Raspberry Pi OS Lite (64-bit) before continuing.

Check the kernel is recent:

```sh
uname -r
```

Expected: `6.6.x` or `6.12.x` with `-v8-16k` or similar.  Anything 6.1 or
newer runs; 6.10 or newer is needed for instant `GET_REPORT` answers (older
kernels answer after 2.5 s with zeros).  The notes in `docs/usb-identity.md`
are written against 6.12.

Reboot once more so you are on the updated kernel:

```sh
sudo reboot
```

Reconnect with SSH after about 30 seconds.

---

## Part 4: Install hid-bridge

### 4.1 Get the code

```sh
cd ~
git clone https://github.com/kirklandsignaturefreezerquartplus/Pi-CM5-Project.git
cd Pi-CM5-Project
```

If the repository is on a branch, check it out as instructed by whoever gave
you the link, e.g. `git checkout claude/eloquent-volta-3036by`.

### 4.2 Run the built-in tests (optional but recommended)

The software has a test suite that needs no hardware:

```sh
python3 -m unittest discover -s tests
```

Expected, after a second or two:

```
..........................................................................
----------------------------------------------------------------------
Ran 102 tests in 0.1s

OK
```

(The exact count grows as tests are added.)  If anything fails here, stop: the code copy is damaged or Python is too old.

### 4.3 Install

```sh
sudo ./install.sh
```

What it does, and what you should see it print:

1. Copies the program to `/opt/hid-bridge` and puts a launcher at
   `/usr/local/bin/hid-bridge`.
2. Writes `/etc/hid-bridge/config.toml` and fills in a random serial number
   (`wrote /etc/hid-bridge/config.toml (serial XXXXXXXXXXXX)`).
3. Tells the kernel to load the two modules it needs at boot.
4. Appends an `[all]` section containing `dtoverlay=dwc2,dr_mode=peripheral`
   (with a comment) to `/boot/firmware/config.txt`.  This switches the USB-C
   connector into device mode.  A backup of the file is kept next to it.
5. Installs and enables two services: `hid-gadget` (creates the virtual
   keyboard/mouse at boot) and `hid-bridge` (forwards input).
6. Runs `hid-bridge check` and prints the descriptors.  One `note:` line
   about the pid.codes test vendor ID is normal at this stage.
7. Prints `Reboot to activate USB device mode:  sudo reboot` (or `Start now
   with: …` when the boot config already had the overlay), followed by a
   `Then check:` line.

Do that:

```sh
sudo reboot
```

### 4.4 Confirm the gadget exists

After reconnecting:

```sh
hid-bridge gadget status
```

Expected (abridged):

```json
{
  "gadget": "/sys/kernel/config/usb_gadget/hidbridge",
  "exists": true,
  "bound": true,
  "patched_kernel": false,
  "descriptor": { "idVendor": "0x1209", "idProduct": "0x0001", ... },
  "functions": {
    "keyboard": { "protocol": "1", "subclass": "1", "report_length": "8", ... },
    "mouse":    { "protocol": "2", "subclass": "1", "report_length": "4", ... }
  },
  "udc": { "udc": "1000480000.usb", "state": "not attached", "current_speed": "UNKNOWN", ... },
  "devices": { "keyboard": "/dev/hidg0", "mouse": "/dev/hidg1", ... }
}
```

The important lines: `"bound": true`, and a `udc` block.  `"state": "not
attached"` is correct because nothing is plugged into the USB-C yet.

If instead you see `"exists": false` and `"udcs": []`:

```sh
grep dwc2 /boot/firmware/config.txt      # must show dtoverlay=dwc2,dr_mode=peripheral
lsmod | grep dwc2                        # must list dwc2
sudo systemctl status hid-gadget         # read the error
```

The common cause is that the config.txt line landed under a section header
that does not apply (`[pi4]` for example).  Move it under `[all]` and reboot.

Both services should be running:

```sh
systemctl is-active hid-gadget hid-bridge
```

Expected: two lines, `active` and `active`.

---

## Part 5: Bench test with a plain keyboard (no PiKVM yet)

This proves the whole path works before you involve the switch.  You need the
spare USB keyboard, the USB-C cable with the power blocker, and the target
computer (or any computer).

### 5.1 Plug in a source

Plug the spare keyboard into one of the CM5's USB-A ports.  On the CM5:

```sh
hid-bridge inputs
```

Expected: a table with your keyboard, e.g.

```
PATH              NAME                        ID         KIND      ROLE
/dev/input/event0 Dell KB216 Wired Keyboard   413c:2113  keyboard  passthrough [default passthrough]
```

Watch the bridge take it over:

```sh
journalctl -u hid-bridge -n 5
```

Expected: a line like `attached /dev/input/event0: 'Dell KB216 Wired Keyboard'
[413c:2113] kbd=True mouse=False abs=False role=passthrough (default
passthrough) grabbed`.

### 5.2 Connect the target

Now connect: **power blocker into the CM5's USB-C**, cable from the blocker to
a USB port on the target computer.  Within a second or two, Windows plays its
device-connected sound.  On the CM5:

```sh
hid-bridge gadget status | grep -E '"state"|"current_speed"'
```

Expected:

```
    "state": "configured",
    "current_speed": "full-speed",
```

`configured` means the target has enumerated the virtual keyboard and mouse.

### 5.3 Type

Open Notepad (or any text field) on the target and type on the spare keyboard
plugged into the CM5.  The letters appear on the target.  Press Caps Lock:
the keyboard's Caps Lock light turns on (the target's lock state is sent back
through the bridge).

Check the counters:

```sh
hid-bridge ctl status
```

Expected, inside `"result"`: `"keyboard": {"device": "/dev/hidg0", "sent": <n>,
"deferred": <n>, "dropped": 0, "host_connected": true, "backing_off": false,
"get_report_cache": true}`, your keyboard listed under `"sources"`, and
`"leds": 2` while Caps Lock is on.  A non-zero `deferred` is normal: it
counts reports that waited for the host's next poll.

If the keyboard types on the target, the software path is proven.  Unplug the
spare keyboard.  Leave the target connected.

### 5.4 Look at it from Windows

Copy `tools/windows/Get-HidBridgeDevices.ps1` to the target (or open it from a
network share) and run it in PowerShell:

```powershell
.\Get-HidBridgeDevices.ps1
```

Expected: a `USB Composite Device`, two `USB Input Device` entries (services
`HidUsb`), one `HID Keyboard Device` (`kbdhid`) and one `HID-compliant mouse`
(`mouhid`), all with driver provider Microsoft and status OK.  This is exactly
what a keyboard with a built-in pointing device looks like to Windows.

---

## Part 6: Connect the PiKVM switch

### 6.1 Cabling

1. On the multiport switch, find the cable for **port N** that currently goes
   to the target computer's USB port.  Unplug it from the target.
2. Plug it into a **USB-A port on the CM5** (with the adapter if its plug is
   USB-C).
3. Leave the switch's HDMI connection for port N exactly as it is.
4. The CM5's USB-C to the target (from Part 5) stays connected.

Nothing else on the switch or PiKVM changes.  Other ports keep working as
before.

### 6.2 Confirm the CM5 sees the switch

```sh
hid-bridge inputs
```

Expected: one or more rows from the switch or PiKVM, typically named `PiKVM
Composite KVM Device` or similar, marked `keyboard` and `mouse` or
`mouse(abs)`.  Rows marked `ignored (not kbd/mouse)` are other functions the
switch or PiKVM exposes (serial, storage); the bridge never forwards them.

If nothing appears, the switch is probably not presenting HID on that port
until it is *selected*: select port N in the PiKVM web interface and run
`hid-bridge inputs` again.

### 6.3 Mouse mode

Decide how the mouse should behave.  Two good configurations:

**Option 1, everything relative (recommended; works in BIOS/UEFI too).**
Set the PiKVM to relative mouse mode.  On the PiKVM (not the CM5), SSH in
(`ssh root@pikvm`), then:

```sh
rw
nano /etc/kvmd/override.yaml
```

Add (or merge into an existing `kvmd:` block):

```yaml
kvmd:
    hid:
        mouse:
            absolute: false
```

Then `ro` and `systemctl restart kvmd`.  In the PiKVM web UI, the mouse now
moves the target's cursor by dragging; the cursor no longer jumps to where
your browser pointer is.  (Consult the PiKVM documentation "Mouse modes" for
your firmware version; if the switch handles HID itself, its own settings
apply.)  Nothing to change on the CM5: `mouse.mode = "relative"` is the
default.

**Option 2, keep PiKVM's absolute pointer.**  On the CM5, edit
`/etc/hid-bridge/config.toml`, set `mode = "absolute"` under `[mouse]`, then
apply (Part 8.1).  The target sees a tablet-style pointer, exactly as it
would from the PiKVM directly.  Not usable in BIOS/UEFI menus.

If you change nothing, the bridge converts PiKVM's absolute positions to
relative movements.  It works, with the caveat that the target cursor and
your browser pointer drift apart.

### 6.4 Test from the PiKVM web UI

1. Open the PiKVM web interface, select port N.
2. Click into the video and type into Notepad on the target.  Text appears.
3. Move the mouse; click; scroll.  All work.
4. Press Caps Lock; the PiKVM UI's lock indicator lights.  Press again to
   clear.
5. Use PiKVM's shortcut menu to send Ctrl+Alt+Del.  The Windows security
   screen appears.  Press Esc.

On the CM5, `hid-bridge ctl status` shows the counters rising and the switch's
devices under `sources`.

### 6.5 Test the BIOS/UEFI path

Restart the target from the PiKVM and press the setup key (Del or F2) via the
PiKVM keyboard at the right moment.  You should enter firmware setup and be
able to move around with the arrow keys and, in graphical setups, the mouse
(with Option 1 above).  This confirms the boot-protocol path that a composite
KVM gadget sometimes fails.

Boot back into Windows.

---

## Part 7: Verify what the target sees (identity check)

You have already seen Device Manager's view in 5.4.  For a byte-level check,
install Microsoft's **USBView** (part of the Windows SDK / Debugging Tools) or
Thesycon's **USB Descriptor Dumper** on the target and select the device.
Compare with the CM5's own view:

```sh
tools/verify-gadget.sh
hid-bridge check
```

What to compare:

| Field | Expected |
|---|---|
| Speed | Full-speed (12 Mb/s) |
| bcdUSB | 2.00 (or 2.01 with a BOS descriptor if `lpm (debugfs)` shows 1 on the CM5; always 2.00 without BOS once `kernel-patches/0002` is installed) |
| bDeviceClass/SubClass/Protocol | 0 / 0 / 0 |
| idVendor / idProduct | as in `[gadget]` (0x1209 / 0x0001 until you change them) |
| Configuration bmAttributes / MaxPower | 0xA0 / 100 mA |
| Interface 0 | Class 3, SubClass 1, Protocol 1, one Interrupt IN endpoint |
| Interface 1 | Class 3, SubClass 1, Protocol 2, one Interrupt IN endpoint |
| Report descriptors | the hex bytes printed by `hid-bridge check` |

`docs/usb-identity.md` explains every field, including the few the kernel
decides on its own and how to remove those with the optional patches in
Part 9.

---

## Part 8: Configuration

The single configuration file is `/etc/hid-bridge/config.toml`.  Edit it
with `sudo nano /etc/hid-bridge/config.toml`.  It is fully commented.

### 8.1 Applying changes

Changes under `[bridge]`, `[[inputs]]` and `[macros]` need only the bridge
restarted, which the target does not notice:

```sh
hid-bridge check                       # validates the file first
sudo systemctl restart hid-bridge
```

Changes under `[gadget]`, `[keyboard]` or `[mouse]` change the USB
descriptors, so the target must re-enumerate:

```sh
hid-bridge check
sudo systemctl restart hid-gadget hid-bridge
```

then unplug the USB-C cable from the target and plug it back in (Windows
caches descriptors per port until the device disconnects).

### 8.2 Identity: vendor ID, product ID and strings

Out of the box the bridge uses the pid.codes *test* ID `0x1209:0x0001`.
Windows and firmware do not care, but a USB ID lookup labels it a test device.
To look exactly like a specific keyboard/mouse combo you own:

1. On any Linux machine with that device plugged in (the CM5 itself works;
   plug the reference keyboard into a USB-A port):

   ```sh
   lsusb                                    # find its VVVV:PPPP
   lsusb -v -d VVVV:PPPP > reference.txt
   tools/identity-from-lsusb.py reference.txt
   ```

2. Paste the printed `[gadget]` block over the one in `config.toml`.  The
   serial is randomised for you so the two devices never collide.
3. Apply per 8.1 (gadget change: restart both, replug).

Read `docs/remaining-tells.md` §1 first: use only IDs of hardware you own,
and avoid brands whose software is installed on the target.

### 8.3 Speed, keyboard and mouse options

| Setting | Default | Change it when |
|---|---|---|
| `gadget.max_speed` | `full-speed` | You want a self-consistent USB 2.0 high-speed device with 1 ms polling (`high-speed`) |
| `gadget.remote_wakeup` | `true` | You are on a stock kernel and want the descriptor to match behaviour (`false`; see Part 9) |
| `keyboard.descriptor` | `boot` | You need F13–F24 or Japanese/Korean keys forwarded (`extended`) |
| `mouse.mode` | `relative` | You want PiKVM's absolute pointer end-to-end (`absolute`) |
| `mouse.buttons` | `3` | You use back/forward mouse buttons through PiKVM (`5`) |
| `mouse.abs_to_rel_resolution` | `[1920, 1080]` | Converting absolute to relative and the target's desktop is a different size |
| `mouse.rel_to_abs_gain` | `17.0` | A relative mouse drives an `absolute` output and moves too fast or too slow |
| `bridge.macro_jitter_ms` | `30` | Macro cadence should be more or less random (`0` = fixed timing) |
| `bridge.log_level` | `info` | You want `debug` detail in the journal |
| `[[inputs]].grab` | inherits `bridge.grab_inputs` | One device must stay usable on the CM5 itself while still being read |

Rarely changed: `gadget.self_powered` (false), `gadget.max_power_ma` (100),
`gadget.udc` (auto), `gadget.name` (configfs directory), and the two
`poll_interval_ms` values, which only take effect on kernels whose HID
function has an `interval` attribute (rpi-6.12.y does not).

### 8.4 Excluding a device

To keep a keyboard for administering the CM5 locally, or to stop a device
being forwarded, add a rule.  Find its name or IDs with `hid-bridge inputs`,
then:

```toml
[[inputs]]
name = "^Dell KB216"      # regular expression on the device name
role = "ignore"
```

Rules are tried top to bottom; the first match wins; unmatched devices are
forwarded.  Restart the bridge (8.1).  Then the Dell keyboard works on the
CM5's own console again.

---

## Part 9: Optional hardening (kernel patches and physical tells)

Everything so far gives a device that Windows, Linux and UEFI treat as an
ordinary keyboard and mouse.  A specialist with a USB protocol analyser could
still spot a few details decided inside the Linux kernel.  `kernel-patches/`
removes them; `docs/remaining-tells.md` covers what is not software.

### 9.1 Should you do this?

Do it if any of these matter to you: a byte-exact descriptor match, a key
press waking a sleeping target (remote wakeup), or an inspector with analyser
equipment.  Skip it if you just want reliable KVM control with UEFI access.

### 9.2 Build the patched kernel on the CM5

Follow `kernel-patches/README.md`.  In outline (60 to 90 minutes, mostly
waiting):

```sh
sudo apt install -y git bc bison flex libssl-dev make libc6-dev libncurses5-dev
cd ~
git clone --depth=1 --branch rpi-6.12.y https://github.com/raspberrypi/linux
cd linux
git apply ~/Pi-CM5-Project/kernel-patches/*.patch
make bcm2712_defconfig
make -j"$(nproc)" Image.gz modules dtbs
sudo make modules_install
sudo cp /boot/firmware/kernel_2712.img /boot/firmware/kernel_2712-stock.img
sudo cp arch/arm64/boot/Image.gz /boot/firmware/kernel_2712.img
sudo cp arch/arm64/boot/dts/broadcom/*.dtb /boot/firmware/
sudo cp arch/arm64/boot/dts/overlays/*.dtb* /boot/firmware/overlays/
sudo reboot
```

Afterwards `hid-bridge check` reports `kernel-patches/ present: yes
(strict_report_types attribute found)`, no longer lists `strict_report_types`
or `wakeup_on_write` as missing, and `tools/verify-gadget.sh` shows both set
to 1.  The remote-wakeup operation
can be exercised without a key press: `echo 1 | sudo tee
/sys/class/udc/*/srp` while the target sleeps.  Hold the kernel package so an update does not replace it:

```sh
apt-mark showhold; dpkg -l | grep linux-image    # find the installed package name
sudo apt-mark hold <that package>
```

If the CM5 fails to boot on the new kernel, put the SD/eMMC into another
machine (or use rpiboot) and rename `kernel_2712-stock.img` back to
`kernel_2712.img`.

Patches 0004 (remote wakeup) and 0005 (standard-request answers) have not
yet been exercised on hardware.  Test 0004
after installing: sleep the target (S3), enable *Allow this device to wake the
computer* under Device Manager → HID Keyboard Device → Power Management, press
a key via PiKVM.  If the target does not wake, set `remote_wakeup = false` in
`config.toml` and report the result.

### 9.3 Physical and operational items

From `docs/remaining-tells.md`, in priority order:

1. **Independent power**: the CM5's PoE injector or 5 V supply must not depend
   on the target being on.  A CM5 that boots before the target's USB
   controller powers up is simply "a keyboard that was there".
2. **Never restart `hid-gadget` or reboot the CM5 while the target is in
   use**; it looks like a keyboard being unplugged.  Restarting `hid-bridge` alone sends nothing on the bus (it only releases keys that were still held).  Turn off unattended reboots:
   `sudo systemctl disable --now unattended-upgrades` or configure it never to
   reboot.
3. **Boot order**: `sudo rpi-eeprom-config --edit`, set `BOOT_ORDER=0xf1`
   (eMMC/SD, then retry forever) so a failed boot never falls into USB
   programming mode.  Save, exit, reboot.
4. **VBUS load**: a 150 to 220 Ω, 0.5 W resistor between 5 V and ground on the
   target side of the power blocker makes the "keyboard" draw a realistic 25
   to 33 mA.  Only relevant if someone might measure current.

---

## Part 10: Macros and extra input devices

### 10.1 One-off commands from the CM5

These work immediately, from any SSH session:

```sh
hid-bridge ctl keys ctrl+alt+delete
hid-bridge ctl type "Hello from the bridge"
hid-bridge ctl steps "win+r" "wait 400" "type notepad" "enter"
hid-bridge ctl macro win_lock
hid-bridge ctl release-all           # if anything ever seems stuck
```

Key names: `ctrl shift alt win`, `enter esc tab space backspace delete
insert home end pageup pagedown up down left right`, `f1`–`f24`, letters,
digits, `kp0`–`kp9`, etc.  `docs/macros.md` has the full list and the step
language.

### 10.2 Defining macros

In `config.toml`:

```toml
[macros]
ctrl_alt_del = ["ctrl+alt+delete"]
win_lock     = ["win+l"]
sim_pause    = ["pause"]
login        = ["ctrl+alt+delete", "wait 1200", "type MyPassword", "enter"]
```

`hid-bridge check` reports any typo; restart the bridge to load them.
Macro taps and gaps already get up to 30 ms of random jitter
(`macro_jitter_ms = 30` under `[bridge]`) so typed macros do not have a
perfectly regular rhythm; raise it, or set 0 to turn it off.

### 10.3 A macro keypad

1. Plug the keypad into a spare USB-A port on the CM5.
2. `hid-bridge inputs` shows it, for example
   `Macro Pad  1a2c:2d43  keyboard  passthrough [default passthrough]`.  Right now its keys would
   be forwarded as ordinary key presses.
3. Find out which key is which: `journalctl -u hid-bridge -f` while pressing
   keys shows nothing by default; instead run `sudo evtest
   /dev/input/eventN` (install with `sudo apt install evtest`) briefly, or use
   the standard names `KEY_1`, `KEY_2`, `KEY_KP0` and adjust.
4. Add a rule:

   ```toml
   [[inputs]]
   label   = "macro pad"
   vendor  = 0x1a2c
   product = 0x2d43
   role    = "macro"
   unbound = "drop"
   [inputs.bindings]
   KEY_1 = "ctrl_alt_del"
   KEY_2 = "win_lock"
   KEY_3 = "sim_pause"
   ```

5. `hid-bridge check`, `sudo systemctl restart hid-bridge`, press a key.

Two identical keypads are told apart with `phys = "..."` (the USB port path
shown by `hid-bridge inputs`).

### 10.4 Scripting from other software on the CM5

Any program on the CM5 can send input by writing one JSON line to
`/run/hid-bridge/ctl.sock` as root:

```sh
printf '{"cmd":"macro","name":"win_lock"}\n' | sudo socat - UNIX-CONNECT:/run/hid-bridge/ctl.sock
```

Home-automation hooks, cron jobs and SSH-triggered scripts all work this way.
Anyone who can run commands on the CM5 can type on the target; keep the
CM5's SSH access as tight as the target's own login.

### 10.5 Flight simulator panels

For the simulator use case there are two placements:

* **Panels plugged into the target directly** (the usual choice): the
  simulator sees them as their own devices, and the KVM input arrives through
  the CM5 as one ordinary keyboard/mouse that never changes identity when you
  switch KVM ports.  Nothing to configure.
* **Panels plugged into the CM5** as macro devices: their switches trigger
  macros (key combinations the simulator has bound), so the simulator only
  ever sees keyboard input.  Use `role = "macro"` rules as in 10.3.

---

## Part 11: Day-to-day operation

### 11.1 Normal use

There is nothing to do.  The CM5 boots, the gadget comes up, the bridge
starts, and the PiKVM controls the target as before.  Power the CM5 from an
always-on supply so it is running before the target boots.

### 11.2 Status and logs

```sh
systemctl status hid-gadget hid-bridge      # services
hid-bridge ctl status                       # live counters, sources, LEDs, macros
hid-bridge ctl inputs                       # attached and ignored devices
journalctl -u hid-bridge -f                 # follow the log
tools/verify-gadget.sh                      # what the CM5 is presenting
```

### 11.3 Updating hid-bridge

```sh
cd ~/Pi-CM5-Project
git pull
python3 -m unittest discover -s tests
sudo ./install.sh                # keeps your config; new defaults land in config.toml.dist
sudo systemctl restart hid-bridge
```

Your `config.toml` is never overwritten.  Compare it with
`/etc/hid-bridge/config.toml.dist` occasionally for new options.

### 11.4 Updating the operating system

`sudo apt update && sudo apt full-upgrade` is safe at any time; only reboot
when the target is not in use.  If you installed the patched kernel (Part 9),
keep the package on hold or rebuild after kernel updates.

### 11.5 Backup

Once everything works, image the CM5's eMMC so a bad update is a 10-minute
restore rather than a rebuild.  With the CM5 powered off, fit the nRPIBOOT
jumper, connect the USB-C to a computer running `rpiboot` (Raspberry Pi
usbboot), and use Raspberry Pi Imager or `dd` to read the whole device to a
file.  Remove the jumper afterwards (Part 2.3).

### 11.6 Stopping or removing

```sh
sudo systemctl stop hid-bridge              # stop forwarding, keyboard stays enumerated
sudo systemctl stop hid-gadget              # keyboard disappears from the target
sudo ./uninstall.sh                         # remove software, keep config and boot setting
sudo ./uninstall.sh --purge                 # remove everything; reboot returns USB-C to normal
```

---

## Part 12: Troubleshooting quick reference

`docs/troubleshooting.md` has the full version.

| Symptom | First thing to check |
|---|---|
| `hid-bridge gadget status` says `"udcs": []` | `dtoverlay=dwc2,dr_mode=peripheral` missing or under the wrong `[section]` in `/boot/firmware/config.txt`; reboot after fixing |
| `"state"` never becomes `configured` | Cable in a USB-A port instead of USB-C; power blocker or cable faulty; try another target port |
| Windows: "Unknown USB Device (Device Descriptor Request Failed)" | Cable/port; `sudo systemctl restart hid-gadget hid-bridge`, replug |
| Typing works from PiKVM but keys arrive on the CM5's console | Device not grabbed; you are running a desktop session, or `grab_inputs = false`; check the journal for `cannot grab` |
| `host_connected: false` in `ctl status` | Target off or not enumerated; reports are dropped until it returns |
| `backing_off: true` in `ctl status`, journal says `host is not accepting reports (bus suspended?)` | Target has suspended the bus (asleep); the bridge retries every 50 ms to 1 s and resumes on its own; motion made while asleep is discarded |
| A key seems stuck on the target | `hid-bridge ctl release-all`, then look at `keys_held` per source in `ctl inputs` |
| Mouse jumps or drifts | PiKVM absolute → bridge relative conversion; pick Option 1 or 2 in Part 6.3 |
| Mouse missing in BIOS setup | `mouse.mode` is `absolute`; switch to `relative` and replug |
| `hid-bridge inputs` shows nothing from the switch | Select port N on the PiKVM; check the switch cable is in a CM5 USB-A port; `lsusb` on the CM5 |
| The CM5 shows up on the target as "BCM2712 Boot" | nRPIBOOT jumper fitted, or boot failed; see Part 2.3 and 9.3 |

---

## Appendix A: Command cheat sheet

```
hid-bridge check                     validate config, print descriptors, kernel feature report
hid-bridge gadget status|up|down     virtual device state / create / remove
hid-bridge inputs                    list attached input devices and their roles
hid-bridge ctl status|inputs         live bridge state
hid-bridge ctl keys COMBO            tap a key combination on the target
hid-bridge ctl type TEXT             type text on the target
hid-bridge ctl steps STEP...         run ad-hoc macro steps
hid-bridge ctl macro NAME            run a configured macro
hid-bridge ctl release-all           release every key and button
tools/verify-gadget.sh               dump what the CM5 presents on the bus
tools/identity-from-lsusb.py [--config CFG] FILE   build a [gadget] block from a reference device, warn where the clone would differ
hid-bridge [-c FILE] [-v] COMMAND    use another config file / debug logging
hid-bridge run [--auto-gadget]       run the daemon in the foreground (what the service does)
tools/windows/Get-HidBridgeDevices.ps1   Windows-side view of the device
sudo systemctl restart hid-bridge    apply [bridge]/[[inputs]]/[macros] changes
sudo systemctl restart hid-gadget hid-bridge   apply [gadget]/[keyboard]/[mouse] changes (then replug)
```

## Appendix B: Where things live

| Path | Purpose |
|---|---|
| `/etc/hid-bridge/config.toml` | your configuration |
| `/etc/hid-bridge/config.toml.dist` | latest shipped defaults for comparison |
| `/opt/hid-bridge/` | the program, docs and tools |
| `/etc/systemd/system/hid-gadget.service`, `hid-bridge.service` | services |
| `/boot/firmware/config.txt` | contains the `dtoverlay=dwc2,dr_mode=peripheral` line |
| `/etc/modules-load.d/hid-bridge.conf` | loads `dwc2` and `libcomposite` at boot |
| `/run/hid-bridge/ctl.sock` | control socket |
| `/run/hid-bridge/gadget.json` | which `/dev/hidgN` is keyboard and which is mouse |
| `/sys/kernel/config/usb_gadget/hidbridge/` | the live gadget definition |

## Appendix C: Acceptance checklist

Tick these off before calling the installation done:

- [ ] `python3 -m unittest discover -s tests` passes on the CM5
- [ ] `hid-bridge gadget status` shows `bound: true`, `state: configured`, `full-speed`
- [ ] Bench keyboard types on the target; Caps Lock light follows the target
- [ ] `Get-HidBridgeDevices.ps1` shows only Microsoft class drivers
- [ ] PiKVM port N: typing, mouse, scroll, Ctrl+Alt+Del, lock indicator all work
- [ ] Target's BIOS/UEFI setup reachable and navigable through PiKVM
- [ ] Other switch ports unaffected
- [ ] CM5 on independent power; nRPIBOOT jumper removed; `BOOT_ORDER` set
- [ ] eMMC image backed up
- [ ] Optional: identity cloned; patched kernel installed and `remote wakeup` tested
````

## docs/hardware.md

`4295 bytes, 86 lines, sha256 e706de9ac63ac45feca8c9464b942ffe0c380df9cb8592d3bdaf51f81f9dc615`

````markdown
# Hardware and cabling

## Ports involved

| Link | From | To | Role |
|---|---|---|---|
| A | PiKVM V4 Plus **OTG/target USB-C** (its HID output) | CM5 carrier **USB-A host port** | PiKVM → CM5 keyboard + mouse |
| B | Macro keypads, control surfaces | CM5 carrier **USB-A host ports** | local sources (optional) |
| C | CM5 carrier **USB 2.0 device port** (USB-C on the CM5 IO Board) | Target PC USB port | CM5 → PC as "USB Keyboard" |
| D | Target PC HDMI | PiKVM HDMI input | unchanged; video never passes through the CM5 |

The CM5 has exactly one USB 2.0 controller that can act as a device: the
BCM2712's dwc2 OTG port, which carriers route to a USB-C connector (on the
official CM5 IO Board that is the USB-C jack also used for USB power/rpiboot).
The USB-A ports come from the RP1 I/O chip and are host-only.  Link C **must**
use the dwc2 port; the bridge cannot present a device on the USB-A ports.

## Boot configuration

`install.sh` appends to `/boot/firmware/config.txt`:

```
[all]
dtoverlay=dwc2,dr_mode=peripheral
```

`dr_mode=peripheral` (not `otg`) matters for the identity goal: in OTG mode the
gadget stack adds an OTG descriptor to the configuration, which no plain
keyboard has.  The modules `dwc2` and `libcomposite` are loaded from
`/etc/modules-load.d/hid-bridge.conf`.

## Power

A PC USB port supplies at most 500 mA (900 mA on USB 3 ports).  A CM5 needs
several times that, so **do not power the CM5 from link C**.

On the official **CM5 IO Board** the USB-C connector is both the power input
(USB-PD, 5 V/5 A) and the only place the USB 2.0 device port appears, so the
kit's power supply and the target PC cannot share it.  Power the board another
way: the PoE+ HAT for the CM5 IO Board with a PoE+ injector (recommended), or a
regulated 5 V/5 A supply into the GPIO header's 5 V pins (check the board
datasheet for your revision), or a carrier with a separate DC input.  Then use
the USB-C for data only.  `docs/GUIDE.md` Part 2 compares the options.

Two things to check on your specific carrier before connecting link C:

1. **VBUS back-feed.**  When the CM5 is powered from its own supply and the PC
   also presents 5 V on the USB-C VBUS pin, the two 5 V rails must not fight.
   Carriers with a proper power mux/ideal diode (the CM5 IO Board has PD input
   circuitry) tolerate it; simple carriers may not.  If in doubt, use a
   "data-only"/"power-blocker" USB-C adapter or a cable with the VBUS line
   opened.  Note that dwc2 does not require VBUS sensing to enumerate on the
   Pi 5 family; with the default `self_powered = false` the configuration
   descriptor declares a bus-powered device drawing `max_power_ma` (100 mA,
   configurable 1–500).
2. **rpiboot straps.**  On the CM5 IO Board the USB-C jack doubles as the
   rpiboot/eMMC-flashing port.  Leave the "nRPIBOOT"/USB-boot jumper in its
   normal position, otherwise the module enumerates as a BCM boot device
   instead of running your OS.

If the PC is powered off, USB ports on many motherboards still supply 5 V and
keep the port idle rather than resetting it.  To the CM5 that looks like a
bus *suspend*, not a disconnect: `hid-bridge ctl status` shows
`udc.suspended: 1` (and `backing_off: true` once something has been typed);
key state waits for the PC to come back, mouse motion is discarded.  A port
that drops or resets shows `host_connected: false` instead.  Both are
harmless.

## PiKVM side

PiKVM's own gadget (link A) is a composite device (keyboard, mouse, sometimes
mass storage, serial and Ethernet).  The CM5 enumerates all of it, but the
bridge only opens keyboard and mouse `evdev` nodes; mass storage or Ethernet
functions are ignored and never reach the PC.  See `docs/pikvm.md` for the
recommended PiKVM settings.

## Recommended physical layout

* Keep link C short and use a certified USB 2.0 cable; a full-speed HID device
  is electrically undemanding but a flaky cable shows up as random
  disconnects in `journalctl -u hid-bridge`.
* If the CM5 also needs an administrative keyboard, plug it into the CM5 and
  add an `[[inputs]]` rule with `role = "ignore"` for it, otherwise it too is
  forwarded to the PC.
* Ethernet or Wi‑Fi on the CM5 is only for administration (SSH, updating the
  config).  Nothing on the network path touches the USB identity.
````

## docs/pikvm.md

`3136 bytes, 86 lines, sha256 9b3eb717872ff667ed656a0cdd0c356bd710b6ce3b431111000a9e014d728b07`

````markdown
# PiKVM V4 Plus settings

The PiKVM keeps working exactly as before: its web UI, HDMI capture, and its
own USB gadget are unchanged.  The only difference is that its OTG cable now
plugs into the CM5 instead of into the target PC.

## Mouse mode

The bridge's default output is a **relative** boot-protocol mouse.  PiKVM's
default is an **absolute** pointer.  The bridge converts absolute → relative
automatically (`mouse.abs_to_rel_resolution` sets the virtual screen size),
but the conversion is inherently imperfect: each new absolute sample becomes
a movement relative to the previous one (only the very first sample after
the device attaches is an anchor), so when the browser cursor re-enters the
video frame the PC cursor moves by the difference, and host-side pointer
acceleration and screen-edge clipping make the two positions drift apart.
Two clean options:

1. **Switch PiKVM to relative mode** (best for UEFI and for games/simulators
   that capture the cursor).  In the PiKVM web UI: *System → Mouse → Relative*,
   or persist it in `/etc/kvmd/override.yaml`:

   ```yaml
   kvmd:
       hid:
           mouse:
               absolute: false
   ```

   (Key names follow the PiKVM documentation for your kvmd version; check
   `kvmd -m` after editing.)

2. **Switch the bridge to absolute mode** to keep PiKVM's absolute pointer
   end-to-end: set `mouse.mode = "absolute"` in `/etc/hid-bridge/config.toml`
   and restart `hid-gadget` and `hid-bridge`.  The PC then sees a
   tablet-style pointer (like PiKVM's own), which is not a boot mouse and is
   not usable in firmware menus.  A relative source in this mode (PiKVM in
   relative mode, a local mouse, `mouse move` steps) drives a virtual cursor
   that starts at the centre and moves `mouse.rel_to_abs_gain` units
   (of 0..32767) per count.

## Functions the CM5 ignores

PiKVM's gadget can also expose mass storage, a serial console and USB Ethernet.
The CM5 enumerates them but `hid-bridge` only opens keyboard and mouse
`evdev` nodes, so nothing of the sort reaches the PC.  You may disable them in
PiKVM to keep the bridge's `hid-bridge inputs` listing tidy, e.g.

```yaml
kvmd:
    msd:
        type: disabled
otg:
    devices:
        serial:
            enabled: false
        ethernet:
            enabled: false
```

## Lock LEDs

When the PC toggles Caps/Num/Scroll Lock (or Compose/Kana), the LED state
arrives at the CM5 as a keyboard output report and is written back to every
attached keyboard that reports that LED, including PiKVM's keyboard
interface and any keyboard attached later, so the PiKVM web UI shows the
same lock indicators it would show if connected directly.  Controlled by
`bridge.forward_leds` (default true).

## Identifying the PiKVM's devices on the CM5

```sh
hid-bridge inputs
```

The PiKVM interfaces appear with a name such as `PiKVM Composite KVM Device`
(vendor 1d6b) and phys paths under the CM5 host port they are plugged into.
No rule is needed for pass-through; add one only if you want to pin behaviour
by port:

```toml
[[inputs]]
label = "PiKVM on port 1"
phys = "usb-xhci-hcd\\.1-1/"
role = "passthrough"
```
````

## docs/usb-identity.md

`13580 bytes, 176 lines, sha256 60c0f80f61a8eb11cf93b70113a7eef5d158b9d8c9acfea46be2f4523e81396f`

````markdown
# USB identity: what is pinned, what the kernel fixes, how to verify

Goal: the PC sees **only a plain USB keyboard and mouse**, down to the control
transfers of enumeration.  This is the honest accounting of that goal against
the Linux gadget stack the CM5 runs (`libcomposite`, `usb_f_hid`, `dwc2`),
checked against the Raspberry Pi `rpi-6.12.y` kernel sources.

## Pinned by hid-bridge

| Descriptor / behaviour | Value | Notes |
|---|---|---|
| Link speed | full-speed (default) or high-speed | `gadget.max_speed`; see "Speed choice" |
| bDeviceClass / SubClass / Protocol | 0 / 0 / 0 | class defined at interface level, as every keyboard does |
| idVendor / idProduct / bcdDevice | configurable | Windows and UEFI bind boot HID by class; the IDs only appear in Device Manager hardware IDs |
| Strings | manufacturer, product, serial | all three set (install writes a random serial) or none; see "Strings" |
| iConfiguration | 0 | never set |
| bNumConfigurations | 1 | |
| Configuration bmAttributes / MaxPower | 0xA0 (bus powered + remote wakeup), 100 mA | configurable |
| OTG descriptor | absent | requires `dr_mode=peripheral`, which `install.sh` sets |
| Interfaces | 2: HID boot keyboard, HID boot mouse | link order fixes interface numbers 0 and 1 |
| Endpoints | one interrupt IN per interface | `no_out_endpoint = 1`: LED output travels over EP0 `SET_REPORT`, exactly as with real boot keyboards |
| wMaxPacketSize | 8 (keyboard), 4 (mouse) | `usb_f_hid` uses the report length |
| Report descriptor (keyboard) | 63 bytes, HID 1.11 Appendix E.6, byte for byte | `keyboard.descriptor = "boot"`; a unit test asserts equality |
| Report descriptor (mouse) | boot mouse + wheel | the first 3 report bytes are the boot format |
| Report IDs | none | |
| `GET_REPORT(Input)` | current key / button state, immediately | the bridge keeps `usb_f_hid`'s GET_REPORT cache current (`GADGET_HID_WRITE_GET_REPORT`, kernel ≥ 6.10); without it the kernel would stall the request for 2.5 s and answer zeros |
| `GET_REPORT(Output/Feature)`, `SET_REPORT(Input/Feature)`, undeclared report IDs, `SET_REPORT(Output)` to the mouse | STALL, like a device with only the declared reports | `strict_report_types` from `kernel-patches/0003`; stock kernels answer them |
| iInterface | 0 | `kernel-patches/0001`; stock `usb_f_hid` attaches a "HID Interface" string |
| `GET_STATUS(Device)` before configuration, `SET_FEATURE(REMOTE_WAKEUP)` without the bit, `TEST_MODE` at full speed, `GET_STATUS(Interface)` for a bad index | bus-powered / STALL / STALL / STALL, like a real device | `kernel-patches/0005`; stock kernels answer them |
| Interrupt IN traffic at start/stop of the bridge | none | no report at start-up; only held keys are released at shutdown |
| Zero-length packet after each report | none, one packet per report | `kernel-patches/0001`; stock `usb_f_hid` terminates every full-size report with a ZLP, visible on an analyser and costing one poll slot per report |
| `SET_PROTOCOL` / `GET_PROTOCOL` | accepted on both boot interfaces | `usb_f_hid` stores it; our reports already are boot format so nothing changes |
| `SET_IDLE` / `GET_IDLE` | accepted | idle-rate re-sends are not implemented by `usb_f_hid`; Windows and UEFI set idle 0 anyway |
| LED `SET_REPORT` | 1 byte over EP0 | forwarded to the PiKVM keyboard as EV_LED |
| Microsoft OS string descriptor (0xEE) | STALL | `os_desc` / WebUSB never configured |

## Fixed by the kernel (not changeable from user space)

| Field | Typical real keyboard | What the CM5 reports | Where |
|---|---|---|---|
| bcdUSB | 0x0110 or 0x0200 | 0x0200; 0x0201 plus a BOS descriptor with a USB 2.0 Extension (LPM) capability if the dwc2 core has LPM enabled | `composite.c` recomputes it from the gadget's capabilities; `dwc2` sets `lpm_capable` from the hardware's `lpm_mode`; `kernel-patches/0002` keeps 0x0200 without BOS at full speed |
| bMaxPacketSize0 | 8 or 64 | 64 | `composite.c` copies dwc2's EP0 size (`EP0_MPS_LIMIT`) |
| bcdHID | 0x0110 | 0x0101 | constant in `usb_f_hid`; `kernel-patches/0001` |
| bInterval | 8–10 ms (FS) | 10 ms at full speed, 1 ms at high speed | constants in `usb_f_hid`; the `poll_interval_ms` options only take effect on kernels that add an `interval` attribute |
| DEVICE_QUALIFIER / OTHER_SPEED_CONFIGURATION at full speed | STALL (FS-only device) | answered (qualifier says high-speed capable) | dwc2 derives `gadget.max_speed` from `params.speed` only at probe; the configfs `max_speed` reaches `dwc2_gadget_set_speed`, which lowers `params.speed` but not `gadget.max_speed`; STALLed with `kernel-patches/0002`, which consults the composite driver's limit |
| Remote wakeup | bit advertised and functional | bit advertised, **not functional** on a stock kernel | dwc2's gadget ops have no `.wakeup` and `usb_f_hid` has no `wakeup_on_write` in 6.12; `kernel-patches/0004` adds both |
| iInterface | 0 | string index pointing at "HID Interface" | constant in `usb_f_hid`; `kernel-patches/0001` |
| `GET_STATUS(Device)` in the Address state | bus-powered | self-powered | `composite_dev_prepare` sets it at bind; `kernel-patches/0005` |
| Remote-wakeup enable after a bus reset | cleared (USB 2.0 9.1.1.6) | still set if the host had enabled it | dwc2 never clears it on reset; `kernel-patches/0005` |
| `SET_FEATURE(REMOTE_WAKEUP)` with `remote_wakeup = false` | Request Error | ACKed | dwc2 has no `.set_remote_wakeup`; `kernel-patches/0005` |
| `SET_FEATURE(TEST_MODE)` at full speed | Request Error | entered | dwc2; `kernel-patches/0005` |
| `GET_STATUS(Interface 9)` | Request Error | 0x0000 | dwc2 answers without checking; `kernel-patches/0005` |
| `GET_IDLE` before the host's `SET_IDLE` | 125 (500 ms) recommended | 1 on stock, 0 with `kernel-patches/0001` | documented deviation; a 500 ms rate would require periodic re-sends |
| Interrupt IN transactions per report | 1 | 2 (report, then a zero-length packet) | `f_hidg_write` sets `req->zero`; `kernel-patches/0001` |
| Unset strings | absent (index 0) | index allocated, empty string descriptor | `libcomposite` substitutes "" for unset strings once the language directory exists |

Windows' HID class drivers and UEFI boot-keyboard drivers inspect none of
these.  `bMaxPacketSize0 = 64`, `bInterval = 10 ms` and `bcdUSB 2.00` are
common in genuine keyboards; the remaining rows are Linux-gadget tells,
visible only to a descriptor dumper or a protocol analyser, which the
patches remove.  The qualifier answer on a stock kernel is tolerated by
every host (a high-speed capable device attached at full speed is a legal
state).

`hid-bridge check` and `tools/verify-gadget.sh` read dwc2's debugfs
`params` to tell you whether LPM is on, i.e. whether the wire shows 2.00 or
2.01 + BOS.

If a byte-exact USB 1.1 match (`bcdUSB 1.10`, `bMaxPacketSize0 8`) is
required as well, the routes are a further kernel patch (an 8-byte EP0 in
dwc2 at full speed, and `composite_setup` honouring the configfs `bcdUSB`
when the driver is limited to full speed; see "What the patches do not
touch" in `kernel-patches/README.md`) or `raw-gadget`, where user space
answers every control request itself.  Neither is written.

## Deep inspection: what could still give the CM5 away

Assume an inspector with a hardware USB analyser, a descriptor dumper and a
USB ID database.  Nothing on the bus says "Raspberry Pi" or "Linux"; the
residual tells are indirect:

| Tell | Who sees it | Status |
|---|---|---|
| `bcdHID 1.01`, `GET_IDLE = 1`, qualifier answered at full speed, `bcdUSB 2.01` + BOS when LPM is on: together they fingerprint "Linux `usb_f_hid` on a dwc2 controller", i.e. a Raspberry Pi class board | analyser / dumper | **fixed by `kernel-patches/`** (kernel rebuild required) |
| VID:PID `1209:0001` resolves to "pid.codes Test PID" in `usb.ids` | `lsusb`, USBView, any ID lookup | **your decision**: set `gadget.vendor_id/product_id`; `hid-bridge check` reminds you while the test ID is in use |
| `GET_REPORT` for Output/Feature reports or undeclared report IDs and `SET_REPORT` for Input/Feature reports (or Output to the mouse) are accepted (real devices STALL them); `SET_REPORT` of any type lands in the LED path | analyser sending malformed class requests | **fixed by `kernel-patches/0003`** (`strict_report_types`, enabled automatically by `hid-bridge gadget up` when present); on a stock kernel the bridge additionally ignores any non-1-byte report in the LED path |
| Remote wakeup advertised but a key press does not wake a suspended PC | functional test | **`kernel-patches/0004`** (dwc2 `.wakeup` + f_hid `wakeup_on_write`; applies cleanly, untested on hardware); otherwise set `remote_wakeup = false` |
| VBUS current ≈ 0 mA while declaring bus-powered 100 mA | USB power meter | hardware: the CM5 runs from its own supply |
| The keyboard appears 15–25 s after the CM5 gets power and disconnects/reconnects whenever the CM5 or `hid-gadget.service` restarts | anyone watching enumeration | operational: power the CM5 before the PC, do not reboot it mid-session |
| With the nRPIBOOT strap fitted (or boot media missing on some carriers) the BCM2712 boot ROM enumerates as a Broadcom boot device (`0a5c:2712`) on the same port | anyone | hardware: keep nRPIBOOT unfitted and boot media reliable |
| Macro `type` steps with a fixed cadence, or modifier and key landing in the same report, look machine-generated | timing / report-sequence analysis of typed text | modifiers now lead and follow the key in their own reports; `bridge.macro_jitter_ms` (default 30) adds right-skewed jitter |
| D+ pull-up present while the PC port is unpowered, and attach with zero delay after port power-on (with the VBUS-blocking adapter the CM5 never sees the PC's 5 V) | meter on D+ with the port off; analyser timing VBUS-on to attach | hardware/operational: sense the PC's VBUS on a CM5 GPIO and drive `/sys/class/udc/<udc>/soft_connect`; see `docs/remaining-tells.md` §6 |
| A `GET_REPORT` arriving while `hid-bridge.service` is stopped is answered after 2.5 s with zeros | analyser, only in that window | `hid-bridge gadget up` primes the GET_REPORT cache when it creates the gadget |

Recommended solves for every row that is not purely software are in
`docs/remaining-tells.md`.

Everything else — descriptors, report formats, boot-protocol handling,
`GET_REPORT` answers, LED handling, string set, endpoint layout — matches a
real two-interface keyboard/mouse device.

## Speed choice

* **full-speed** (default): 12 Mbit/s like real keyboards and mice, 10 ms
  polling, boot-protocol behaviour identical to a real FS device.  Deviation
  on a stock kernel: the qualifier answer above (removed by
  `kernel-patches/0002`).
* **high-speed**: a fully self-consistent USB 2.0 high-speed device with 1 ms
  polling (what gaming keyboards do).  Deviation: generic keyboards are not
  high-speed.  UEFI handles high-speed HID on any EHCI/xHCI controller.

Switch with `gadget.max_speed`, then `systemctl restart hid-gadget hid-bridge`
and re-plug the PC side.

## Strings

`libcomposite` allocates iManufacturer=1, iProduct=2, iSerialNumber=3 as soon
as the `strings/0x409` directory exists and answers unset entries with an
empty string descriptor.  Real keyboards either have all their strings or
none, so `hid-bridge` warns when only some are set.  `install.sh` writes a
random 12-digit hexadecimal serial into a fresh config so every unit is
unique, as with a real product.  To ship no strings at all, clear all three.

## Verifying from the target PC

### Windows (no admin needed)

```powershell
# from tools\windows\ on the PC
.\Get-HidBridgeDevices.ps1 -Vid 1209 -Pid 0001
```

Expected: one `USB Input Device` per interface bound to `HidUsb`, plus
`HID Keyboard Device` (service `kbdhid`) and `HID-compliant mouse`
(`mouhid`), all with driver provider Microsoft.  Hardware IDs look like
`USB\VID_1209&PID_0001&REV_0100&MI_00` and `...&MI_01`; the `MI_` suffix is how
Windows names interfaces of any multi-interface device, keyboards with
integrated pointing devices included.

For the raw descriptors use **USBView** from the Windows SDK or **Thesycon USB
Descriptor Dumper**.  Check: `bcdUSB 2.00` (or `2.01` with a BOS descriptor),
`bDeviceClass 0`, one configuration with `bmAttributes 0xA0`, two interfaces
of class 3 with subclass 1 and protocols 1 and 2, one interrupt IN endpoint
each, and report descriptors matching the hex printed by `hid-bridge check`
on the CM5.

### Linux host

```sh
lsusb -d 1209:0001 -v            # descriptors
sudo usbhid-dump -d 1209:0001    # raw report descriptors
```

`lsusb -t` shows the device at **12M** (full-speed) or **480M** (high-speed).

### On the CM5

```sh
tools/verify-gadget.sh          # configfs values, UDC state, speed, LPM, hidg nodes
hid-bridge gadget status        # same as JSON
hid-bridge check                # config + descriptor hex + kernel feature report
```

`state` must read `configured` and `current_speed` `full-speed` (or
`high-speed`) while the PC is on.

## UEFI / pre-boot behaviour

UEFI keyboard drivers require class 3, subclass 1 (boot), protocol 1, an
interrupt IN endpoint and 8-byte boot reports, all satisfied.  Firmware that
issues `SET_PROTOCOL(boot)` gets identical reports, and a `GET_REPORT` during
initialisation is answered immediately from the cache.  Mouse support in setup
menus additionally needs protocol 2 with 3-byte boot reports, which the
default `mouse.mode = "relative"` provides.  The `absolute` mode is a tablet
style pointer (subclass 0, protocol 0), which firmware ignores; use it only
when the OS is running.
````

## docs/remaining-tells.md

`10440 bytes, 192 lines, sha256 a4223e93943013f959cb2354be66f007f15e3edb0b2595a09129f2a6d8c60a44`

````markdown
# Remaining deep-inspection tells and recommended solves

Status after the software work and `kernel-patches/0001`–`0005`: nothing on the
USB bus identifies the device as Linux, a gadget, or a Raspberry Pi.  What is
left is either an operator decision, a hardware measurement, or a timing
observation.  For each: what an inspector sees, the recommended solve, and
the trade-off.

## 1. Vendor/product ID reads "pid.codes Test PID"

**Seen by:** `lsusb`, USBView, any tool with a USB ID database.  Not by
Windows or UEFI, which bind HID by class.

**Recommended:** clone the USB identity of a keyboard/mouse combo you
physically own.  Dump it with `lsusb -v -d VVVV:PPPP` on any Linux machine
(or USBView on Windows), then

```sh
tools/identity-from-lsusb.py dump.txt        # prints a ready [gadget] block
```

and paste the block into `/etc/hid-bridge/config.toml`.  This copies
idVendor, idProduct, bcdDevice, the three strings and the power attributes,
so the CM5 is indistinguishable from that unit by ID lookup.  It also
prints a `# WARNING` for every point where the reference's descriptor tree
(bcdUSB, EP0 size, interface count, class triples, endpoints, polling
interval, packet size, bcdHID, report-descriptor length) differs from what
hid-bridge will present; pass `--config /etc/hid-bridge/config.toml` so the
comparison uses your actual settings.  Keep a *different* serial from the
physical unit so Windows never sees two instances with the same serial if
both are ever attached.

**Trade-offs:**
* The VID belongs to that vendor.  Using it on your own private hardware has
  no technical consequence, but do not distribute or sell a device carrying
  it; it would be an impersonation of their product.
* Pick a unit whose Windows support is the in-box class driver only.  If the
  target has vendor software installed (Logitech G HUB, Razer Synapse,
  Corsair iCUE…), that software will recognise the VID:PID and try
  vendor-specific HID traffic; the mismatch is then visible to it and it may
  misbehave.  Plain office keyboards and generic 2.4 GHz receivers are safe.
* Alternative with no third-party ID: keep `0x1209:0x0001` and accept that
  ID lookups say "test device", or register a free pid.codes PID (still
  listed under pid.codes).  A private USB-IF vendor ID costs several
  thousand dollars.

## 2. VBUS current is ≈ 0 mA while declaring bus-powered, 100 mA

**Seen by:** a USB power meter or an analyser with current measurement.
Never by software (`MaxPower` is an upper bound, so nothing is violated).

**Recommended:** put a small resistive load across VBUS and GND on the
PC-facing side of the data-only adapter or cable that already isolates the
CM5's supply from the PC's 5 V (see `docs/hardware.md`):

| Resistor | Idle draw | Dissipation | Looks like |
|---|---|---|---|
| 220 Ω, 0.25 W | ≈ 23 mA | 0.11 W | office keyboard / receiver idle |
| 150 Ω, 0.5 W | ≈ 33 mA | 0.17 W | keyboard with lock LEDs lit |
| 100 Ω, 0.5 W | ≈ 50 mA | 0.25 W | backlit keyboard |

Bus-powered devices may draw up to 100 mA before configuration and their
declared `MaxPower` after; keep the load at or below 100 mA (≥ 50 Ω).  Use a
metal-film part inside the adapter shell or a small breakout board.  Do
**not** power the CM5 from VBUS instead; it needs several times what a USB
2.0 port provides.

**Trade-off:** a resistor draws the same current in suspend, whereas a real
keyboard drops to ≤ 2.5 mA when the host suspends the bus.  A meter watching
suspend current would still notice.  Solving that needs a switched load
driven by a CM5 GPIO from the gadget's suspend state, which libcomposite
exports as `/sys/class/udc/<udc>/gadget/suspended` (a symlink to the
`gadget.N` device under the controller, also reachable as
`/sys/bus/gadget/devices/gadget.N/suspended`).  Two caveats for whoever
builds it: the attribute is poll-only (no `sysfs_notify`), and USB 2.0
§7.1.7.6 gives a device 10 ms to reach suspend current, so it needs its own
fast poll rather than the bridge's 1 s rescan; and the file exists only
while the gadget is bound.  The bridge itself reads the same attribute to
tell a suspended bus from a busy one.

Alternative: declare `self_powered = true` and `max_power_ma = 2`.  Honest
and consistent with the meter, but self-powered keyboards are rare, so it is
a descriptor tell instead of a current tell.

## 3. Remote wakeup advertised but a key press does not wake the PC

**Seen by:** a functional test (suspend the PC with "allow this device to
wake the computer" enabled, press a key).

**Recommended:** build the kernel with `kernel-patches/0004`.  It adds the
missing dwc2 gadget `.wakeup` operation and a `wakeup_on_write` option to
`usb_f_hid`; `hid-bridge gadget up` already enables that option when the
kernel has it, and `remote_wakeup = true` (default) keeps the descriptor bit.
The patch is written against `rpi-6.12.y` and applies cleanly, but it has
**not been exercised on CM5 hardware yet**.  Test procedure after
installing it: suspend the PC (S3), enable wake in Device Manager → HID
Keyboard Device → Power Management, press a key on the PiKVM, confirm the PC
resumes and `journalctl -k | grep -i "remote wakeup"` shows the dwc2 debug
line (enable dynamic debug for `dwc2` to see it).

The wakeup operation can also be exercised without a key press: `echo 1 |
sudo tee /sys/class/udc/*/srp` calls it directly.  It only signals when the
PC has the bus suspended and had enabled remote wakeup; otherwise it returns
`-EINVAL` silently (visible with dynamic debug for `dwc2`).

**If you would rather not run a patched kernel:** set `remote_wakeup =
false`.  The descriptor then says 0x80 (no wakeup) and Windows offers no
wake option.  Note that a stock dwc2 still ACKs `SET_FEATURE(REMOTE_WAKEUP)`
if a host sends it anyway; `kernel-patches/0005` makes it STALL as a real
device without the bit would.  Keyboards without remote wakeup exist but
are the minority.

## 4. Keyboard appears 15–25 s after power and reconnects when the CM5 restarts

**Seen by:** anyone watching enumeration at power-on, or Windows' device
arrival sound / Event Log during a session.

**Recommended:**
1. Power the CM5 from a supply that is independent of the PC: on the CM5 IO
   Board that means the PoE+ HAT with an always-on PoE+ injector, or a 5 V
   supply into the header (`docs/GUIDE.md` Part 2; the board has no separate
   DC jack).  The CM5 is then long booted before the PC's USB controller
   powers up, and the PC sees a keyboard that was simply present, exactly as
   with a real one.  This removes the tell entirely for normal use.
2. Do not restart `hid-gadget.service` or reboot the CM5 while the PC is in
   use.  Restarting `hid-bridge.service` alone is safe: the gadget stays
   bound, nothing is sent at start, and at stop only keys or buttons that
   were held are released.  Disable unattended reboots on the CM5
   (`unattended-upgrades` with automatic reboot, `needrestart`).
3. Optional, for cases where the CM5 must boot together with the PC: trim
   boot time.  Raspberry Pi OS Lite reaches `multi-user.target` in roughly
   10–15 s on a CM5; `boot_delay=0` and `disable_splash=1` in `config.txt`,
   masking `NetworkManager-wait-online.service`, and moving
   `hid-gadget.service` to `sysinit.target` with `DefaultDependencies=no`
   (it only needs configfs and the dwc2 module) get the keyboard on the bus
   in about 6–8 s.  UEFI firmware polls for keyboards for several seconds
   during POST, so this is usually enough, but (1) is the robust answer.

## 5. Boot ROM fallback enumerates as a Broadcom boot device

**Seen by:** anyone, as `0a5c:2712 Broadcom Corp. BCM2712 Boot` on the same
port, if the CM5 ever enters USB device boot (rpiboot) mode.

**Recommended:**
1. Leave the nRPIBOOT strap/jumper unfitted on the carrier.  With it fitted
   the boot ROM unconditionally presents the boot device.
2. Pin the EEPROM boot order so a boot failure never falls through to USB
   device boot: `sudo rpi-eeprom-config --edit` and set for example
   `BOOT_ORDER=0xf1` (eMMC/SD, then retry forever) or `0xf6` for NVMe
   carriers.  Mode `3` (RPIBOOT) must not appear in the value.  Ending in
   `f` (restart) instead of `e` (stop) keeps the module retrying silently.
3. Keep the boot medium reliable: eMMC or a good NVMe over a micro-SD card,
   and take an image backup so a corrupted root filesystem is restored
   rather than debugged with the PC attached.

## 6. D+ pull-up without VBUS, and instant attach

**Seen by:** a meter on D+ while the PC's port is unpowered, or an analyser
timing the interval between VBUS appearing and the device attaching.  With
the recommended VBUS-blocking adapter the CM5 never sees the PC's 5 V, so
dwc2 keeps the D+ pull-up asserted whenever the gadget is bound; a real
bus-powered keyboard cannot pull up D+ before VBUS and attaches only after
its controller has started, tens of milliseconds later.

**Recommended:** sense the PC's VBUS on a CM5 GPIO (a two-resistor divider
from the PC side of the blocker to a 3.3 V input) and have a small service
write `disconnect` / `connect` to `/sys/class/udc/<udc>/soft_connect` when
VBUS drops / appears, with a short randomised delay (20–80 ms) after it
appears.  The `soft_connect` attribute is in the stock kernel; only the GPIO
wiring and a few lines of script are new.  Low priority: it needs physical
access to the port while the PC is off.

## 7. Fixed values shared with many real devices (no action)

`bMaxPacketSize0 = 64`, `bInterval = 10 ms` at full speed, string language
0x0409 only, `GET_IDLE` returning 0 (with `kernel-patches/0001`) before the
host sets an idle rate, and
sorted key order in the keyboard array are all found in genuine products and
do not point to a Raspberry Pi.  They are listed here only for completeness.

## Priority order

1. Patched kernel (`kernel-patches/`, ~1 h build) — closes every
   protocol-level tell identified so far, including remote wakeup and the
   standard-request answers, once patches 0004 and 0005 are verified.
2. Independent always-on power for the CM5 — removes the boot-timing tell
   and stabilises everything else.
3. VBUS load resistor in the isolating adapter — cheap, closes the current
   tell for the idle case.
4. Identity choice (`tools/identity-from-lsusb.py`) — your decision.
5. EEPROM `BOOT_ORDER` and jumper check — five minutes, prevents the one
   catastrophic tell.
````

## docs/review-analysis.md

`20093 bytes, 344 lines, sha256 814315a84424c27a7b6fb09f4bc9ab23df8d7fd92caf872b4156fd384ee55306`

```markdown
# Analysis of the external AI code review

An AI code-review tool produced ten findings against this project.  It had
access to three files only: `config/config.toml`, `hid_bridge/gadget.py` and
`docs/remaining-tells.md`.  It did not see `hidg.py`, `bridge.py`, the kernel
patches, `docs/usb-identity.md`, or the kernel sources.  Each finding below is
checked against the actual code and against the Raspberry Pi `rpi-6.12.y`
kernel sources (`drivers/usb/gadget/composite.c`, `configfs.c`,
`function/f_hid.c`, `drivers/usb/dwc2/gadget.c`, `core_intr.c`, `params.c`).
Line numbers refer to those unpatched files.

## Summary

| # | Review item | Claim | Proposed fix | What we did |
|---|---|---|---|---|
| 1 | VBUS current & suspend | restates `remaining-tells.md` §2 | same as ours | corrected the sysfs path we had given for the suspend state |
| 2 | Boot ROM & enumeration timing | restates §4/§5 | same as ours | corrected our own "12 V" wording (the CM5 IO Board has no DC jack) |
| 3 | Hardcoded bcdUSB / bMaxPacketSize0 | tell is real, mechanism wrong | **ineffective**: the kernel overwrites both regardless of configfs | documented; a kernel patch is the only route (offered as a further patch, 0006) |
| 4 | Interface topology & endpoints | premise backwards on OUT endpoints; underlying cloning gap real | over-scoped rewrite | identity tool now diffs the reference's descriptor tree and warns |
| 5 | Remote wakeup | restates §3 / patch 0004 | same as ours | none; the review omits that 0004 is untested on hardware |
| 6 | ConfigFS / f_hid quirks | true in theory, misframed | raw-gadget "custom kernel driver" | not recommended; explained |
| 7 | DWC2 fingerprinting / MCU proxy | justification weak, conclusion strong for other reasons | RP2040 front-end | recommended as the strategic option, with a concrete design |
| 8 | Macro jitter | wrong USB mechanics | kernel module / RTOS | not needed; already handled at the scale that matters |
| 9 | Write-timeout backpressure | mis-stated, but hid a real bug | wrong model (ring buffer) | **fixed**: latest-state model, never blocks, no stuck keys |
| 10 | Mouse quantization | no floating-point aliasing; non-default mode | dithering / 1:1 | 1:1 is already the default; low priority |

Net: three items restate our own residual-tells document, one is factually
wrong about what configfs can do, two are theoretically valid but propose
disproportionate fixes with the wrong justification, two misunderstand USB
interrupt transfers, and two point (with backwards or mis-stated premises) at
real gaps that are now closed.  Reviewing the review also surfaced two
inaccuracies in our own docs, both fixed.

## Item by item

### 1. VBUS current and suspend current

**Claim.** Correct, and identical to `remaining-tells.md` §2 including both
suggested mitigations (resistive load; GPIO-switched load driven by the
suspend state).  Nothing new.

**Correction to our doc.** We had written that `cdev->suspended` is exported
at `/sys/class/udc/*/device/suspended`.  libcomposite creates the attribute
on the *gadget* device (`composite.c:2448`, `device_create_file(&gadget->dev,
&dev_attr_suspended)`), which the UDC core names `gadget.N` under the
controller device (`core.c:1453`), while the `/sys/class/udc/<udc>` link
points at the controller (`core.c:1417-1419`) and also links the gadget
device as `/sys/class/udc/<udc>/gadget` (`core.c:1459-1460`).  The path is
therefore `/sys/class/udc/<udc>/gadget/suspended` (equivalently
`/sys/bus/gadget/devices/gadget.N/suspended`).  Fixed; the bridge now reads
the same attribute to recognise a suspended bus.

### 2. Boot ROM fallback and enumeration timing

**Claim.** Correct and identical to `remaining-tells.md` §4/§5.  The "12 V"
in the review's fix was copied from our own §4, written before we corrected
`hardware.md`: the official CM5 IO Board takes power only through USB-C PD
or the PoE+ HAT (or a 5 V feed on the header), there is no DC jack.  §4 now
says so.

### 3. "Hardcoded" bcdUSB and bMaxPacketSize0

**Claim.** The tell is real (a cloned USB 1.1 keyboard reports bcdUSB 1.10
and an 8-byte EP0; we report 2.00 and 64) and was already listed in
`docs/usb-identity.md` as kernel-fixed.

**Proposed fix is ineffective.** The review suggests parsing both values
from the `lsusb` dump into configfs instead of "hardcoding" them.  The
kernel ignores what configfs holds for these two fields when it answers
`GET_DESCRIPTOR(DEVICE)`:

* `composite.c:1830-1845` (`composite_setup`, `case USB_DT_DEVICE`) sets
  `cdev->desc.bMaxPacketSize0 = cdev->gadget->ep0->maxpacket` and then
  recomputes `bcdUSB` from the gadget's capabilities (0x0200, or 0x0201 with
  LPM, 0x0210/0x0320 for SuperSpeed).  The configfs store
  (`configfs.c:225-238`) writes `cdev.desc.bcdUSB`, but that value is
  overwritten at request time.
* dwc2 fixes EP0 at 64 bytes for full and high speed
  (`gadget.c`, `dwc2_hsotg_irq_enumdone`: `ep0_mps = EP0_MPS_LIMIT` for
  `DSTS_ENUMSPD_FS`/`HS`; `core.h: EP0_MPS_LIMIT 64`); only low speed uses 8.

`gadget.py` writes 0x0200 and 0x40 deliberately so that the configfs tree
shows what is on the wire; the comment in the code says so.  Parsing other
values in would change nothing except make configfs lie.

**What would work.** A kernel patch, which is feasible because the hardware
already supports an 8-byte EP0 (the low-speed path uses it):

1. dwc2: at full speed, use an EP0 packet size of 8 when requested (a DT or
   module parameter, or honour a lowered `ep0->maxpacket_limit`), instead of
   always `EP0_MPS_LIMIT`.  composite then reports 8 automatically since it
   copies `ep0->maxpacket`.
2. composite: when the driver is limited to full speed (which patch 0002
   already uses to suppress the qualifier and LPM), honour the configfs
   `bcdUSB` (1.10) instead of forcing 2.00.

About 20 lines, untested like 0004 and 0005.  Trade-off: an 8-byte EP0
makes enumeration take eight times as many control packets, exactly as a
USB 1.1 keyboard does; no functional impact.  We can add this as patch 0006
on request (0005 has since been used for the standard-request answers); it
only matters when cloning a USB 1.1 reference.

### 4. Interface topology and endpoints

**Premise is backwards.** The review calls the absence of an interrupt OUT
endpoint a tell.  The common design for boot keyboards is exactly one
interrupt IN endpoint with LEDs delivered by `SET_REPORT` on the control
endpoint; an interrupt OUT endpoint is the less common variant.
`no_out_endpoint = 1` therefore matches the typical device, and
`usb_f_hid` supports both (`f_hid.c: use_out_ep`).

**Underlying gap is real.** `tools/identity-from-lsusb.py` cloned VID/PID,
strings and power attributes but said nothing when the reference device's
descriptor *tree* differs from what hid-bridge presents: number of
interfaces (many keyboards have a third, consumer-control interface with
subclass 0/protocol 0), endpoint count, `bInterval`, `wMaxPacketSize`,
`bcdHID`, and the report-descriptor length (a Logitech K120, for instance,
has a 65-byte keyboard descriptor and a 159-byte second interface, not our
63 and 52).  An inspector comparing a cloned VID:PID against a known dump of
that model would see every one of those.

**Fix applied (commit 815bc38).** The tool now parses the reference's
interface, HID and endpoint descriptors and prints a `# WARNING:` line for
each difference, ending with advice to choose a reference with matching
topology.  A "clone mode" that loads report descriptors from files, adds a
consumer-control interface or enables the OUT endpoint per interface is a
possible follow-up; `usb_f_hid` can vary subclass, protocol, report length,
descriptor bytes and the OUT endpoint per function, but not `bInterval`
(`f_hid.c:263,275`, fixed at 10 ms full-speed) or `bcdHID`
(`f_hid.c:145`).  "Rewrite the initialization logic to dynamically construct
interfaces" is the right direction stated as a much larger job than needed.

### 5. Remote wakeup

**Claim.** Correct and identical to `remaining-tells.md` §3 and
`kernel-patches/0004`.  The review omits the material caveat: 0004 applies
cleanly but has not been exercised on hardware.  dwc2 has every register
piece (`gadget.c`, `dwc2_gadget_exit_clock_gating` sets
`DCTL_RMTWKUPSIG`; `core_intr.c`, `dwc2_handle_wakeup_detected_intr`) but
no gadget `.wakeup` operation; 0004 adds it.

### 6. ConfigFS / f_hid "state quirks"

**Claim, checked.** For an invalid string index libcomposite's `get_string`
returns `-EINVAL` (`composite.c:1367`, via `usbstring.c:55`), `composite_setup`
returns the negative value (`composite.c:2308-2309`) and dwc2 stalls EP0
(`gadget.c:2000-2001`, `dwc2_hsotg_stall_ep0`).  Unknown requests take the
same path from the `-EOPNOTSUPP` default (`composite.c:1782`).  That is the
behaviour USB 2.0 §9.2.7 requires of every device, and what the large
majority of keyboard firmware does.

**Framing.** The review's mitigation, emulating a specific ASIC's crash or
garbage responses, is (a) contrary to the project goal of a *generic,
compliant* keyboard, (b) not achievable without first fuzzing the physical
reference device with an analyser to learn its quirks, and (c) misdescribed:
raw_gadget is a small kernel module that hands every SETUP packet to a
user-space program through `/dev/raw-gadget`, so "a custom kernel driver
using raw-gadget" is a contradiction, and even that program cannot change
the handshake and malformed-packet behaviour the dwc2 controller produces.
Device fingerprinting from enumeration behaviour and timing exists
in the research literature, but it needs a per-model baseline; we know of no host
software does this.  Not recommended.

### 7. DWC2 controller fingerprinting and the MCU proxy

**Justification is weak.** An RP2040 has its own electrical and timing
signature; it only "matches the cloned target's cheap controller" if it is
that controller.  Nothing about the dwc2 core's behaviour on edge-case
packets is documented as distinguishable by any host in practice.

**Conclusion is nevertheless the strongest option, for other reasons.** A
small MCU USB front-end (RP2040 with TinyUSB, driven by the CM5 over UART)
would close, without any kernel patch, every item that is hard for the
gadget stack:

* bus-powered from the target, so idle and suspend current are *real*
  (`remaining-tells.md` §2 solved outright, including the GPIO-load idea);
* enumerates within milliseconds of the port powering up, independent of
  the CM5's boot (§4), and the CM5's own USB-C never touches the target, so
  the boot-ROM fallback cannot be seen there (§5);
* every descriptor byte under firmware control: bcdUSB 1.10, EP0 8, bcdHID
  1.10, exact report descriptors, any interface topology (items 3 and 4);
* real remote wakeup through TinyUSB (item 5), no dwc2 patch;
* reports paced by the MCU at the poll rate regardless of Python timing.

PiKVM's own Pico HID (RP2040 + TinyUSB) is prior art.  The bridge already
isolates its output behind one class (`hid_bridge/hidg.py: HidgDevice`, with
`write_report`, `read_output_report`, `poll_readable`, `host_state_changed`
and an `fd`), so a serial sink is a sibling class plus a config switch, not
a rewrite.  Cost: a few hundred lines of firmware, a UART link, and losing
the "pure CM5" simplicity.  This is the recommended path if the remaining
hardware tells matter; otherwise the current design with the five kernel
patches is complete.

### 8. Macro jitter and "microsecond timing"

**Wrong mechanics.** A host cannot measure when user space wrote a report.
It polls the interrupt IN endpoint at `bInterval` and receives whatever
report is waiting: `f_hid.c` fixes that at 10 ms for full speed
(`hidg_fs_in_ep_desc.bInterval = 10`, lines 263/275) and 1 ms at high speed
(`bInterval = 4`, lines 222/234), and it keeps exactly one request in flight
(`write_pending`).  Every observation the host can make is therefore
quantized to the polling interval.  Sub-millisecond scheduler or garbage
collection jitter disappears at 10 ms quantization and shifts at most one
1 ms slot at high speed, which is indistinguishable from any device.

What *is* observable is the cadence in poll units (a fixed 30 ms tap is
always three polls), and `bridge.macro_jitter_ms` already randomizes it
(`macros.py: MacroEngine.tap_delay/gap_delay`).  A kernel module or
real-time proxy would change nothing the host can see.

### 9. Write-timeout backpressure

**Mis-stated in two ways.** Nothing "dropped the connection": after 50 ms of
the previous report not being collected, one *report* was dropped.  And a
hardware "ring buffer overwriting the oldest packet" is the wrong model for
HID: a real keyboard or mouse has one report register; the latest state
wins and motion counts accumulate between polls.

**But the item concealed a real defect.** With `usb_f_hid`'s single in-flight
request (`f_hid.c: f_hidg_write`, `WRITE_COND (!hidg->write_pending)`,
`-EAGAIN` with `O_NONBLOCK`; cleared in the completion handler at line 461
and in `hidg_set_alt` at 1119), the old `hidg.py` (a) blocked the whole
single-threaded loop for up to 50 ms on every second report written within
one poll interval, which any mouse stream above 100 Hz triggers, and (b) if
the host stopped polling for longer than 50 ms, a key-down could stay in
flight while the matching key-up was dropped; when polling resumed the host
received the key-down and nothing else: a stuck key with autorepeat until
the next state change.

**Fix applied (commit 815bc38).** The bridge now holds "what the host should
receive next" per interface: the keyboard report is recomputed from the
merged key state at flush time, relative motion accumulates with saturation
like a mouse's counters, absolute mode keeps the latest position, and
pending state is flushed when `select()` reports the hidg fd writable
(`f_hidg_poll` sets `EPOLLOUT` once `write_pending` clears).  No call blocks,
no state change is lost, idle mouse reports are not repeated, and the
current state is re-sent when the host comes back.  Six new tests cover the
stall scenarios; `write_timeout_ms` is gone.

### 10. Mouse quantization

**Checked.** `rel_to_abs_gain` is used only in relative-source →
absolute-output conversion (`bridge.py: _emit_mouse_motion`, non-default),
where `round(dx * 17.0)` with integer `dx` produces exact multiples of 17;
17.0 is exactly representable, so there is no floating-point aliasing, just a
17-unit position step in a mode that is not recommended.  The default path
(relative in, relative out) passes integer deltas through 1:1, which is the
review's own recommended fix.  Absolute-in → relative-out uses `scale_abs`
(`reports.py`) onto a virtual 1920×1080 screen, producing integer pixel
deltas like any mouse.  Low priority; an integer gain with optional dither
could be added for the rel→abs mode if someone uses it.

## Changes made because of this analysis

* `815bc38` latest-state report model (item 9); identity tool topology
  warnings (item 4); doc corrections (items 1 and 2).
* `7b0c67e` (after the independent verification below): suspend backoff and
  transition FIFOs, reworked patches 0001–0004, new 0005, `GET_REPORT` cache
  priming at `gadget up`, identity tool `--config`, doc corrections.
* This document.

## Independent verification (added after the analysis above)

The ten verdicts were handed to independent verifier agents with the
repository and the kernel sources, and each verdict was then attacked by
two adversarial reviewers (a USB-protocol lens and a Linux-gadget-stack
lens).  Two completeness critics searched the whole project for anything
both the review and the analysis had missed.

**Verdicts.** All ten conclusions held.  Five were marked "materially
incomplete" on specific points, all folded in:

* Item 3: the only workable route to a USB 1.1 clone is lowering dwc2's
  EP0 size and stashing the configfs `bcdUSB` at bind; honouring
  `bMaxPacketSize0` from configfs (as `usb-identity.md` once suggested)
  would advertise a size the controller does not use.
* Item 4: `usb_f_hid` also attaches an interface string ("HID Interface")
  to every interface, a Linux-only tell nobody had listed.  Fixed in
  `kernel-patches/0001`.
* Item 5: the partial-power-down branch of patch 0004 never asserted the
  wakeup signal, the patch dereferenced the composite device before
  checking the function was configured, and it could drive resume inside
  the 5 ms minimum suspend time.  All three fixed in the reworked 0004.
* Item 6: `GET_REPORT` for an undeclared report ID was answered after a
  2.5 s stall with zeros, a timing signature.  Fixed in the reworked 0003.
* Item 7: an RP2040 front-end would not give an 8-byte EP0 out of the box
  (TinyUSB opens EP0 at 64) and the bridge's poll-paced output already
  matches an MCU's; the remaining benefits stand.

**Critics.** The robustness critic found one serious defect in the
latest-state refactor of commit 815bc38: when the host suspends the bus,
dwc2 refuses every queued request with EAGAIN while `poll()` still reports
the fd writable, so the loop would have spun at 100 % CPU with any pending
input until the host resumed.  The bridge now recognises "writable but
refused" as suspension, backs off exponentially, consults libcomposite's
`suspended` attribute before retrying, discards motion made while asleep,
and re-sends the current state on resume.  Also fixed from the same
report: a press-and-release inside one poll interval was coalesced away
(transitions are now queued and replayed in order); motion accumulated
during a long stall replayed as a multi-second cursor burst (it now
saturates to one 8-bit report like a real mouse); the bridge kept stale
`/dev/hidg*` descriptors after a gadget rebuild (they are revalidated every
second); a restart within one poll of a key-down could leave the key
auto-repeating (shutdown now waits briefly for the release to be
collected, and only when something was held); evdev `SYN_DROPPED` was
ignored (state is rebuilt from `EVIOCGKEY`); a control client that connected
without sending could stall the loop for 0.5 s (now 50 ms); a device
reusing an ignored `eventN` path inherited the old verdict (the inode is
tracked); and the mouse re-sync after a host reset was a no-op.

The protocol critic listed the residual request-level tells now closed by
`kernel-patches/0005` (self-powered before configuration, remote-wakeup
feature ACKed without the bit, test modes at full speed, `GET_STATUS` for a
non-existent interface), the mouse interface accepting `SET_REPORT(Output)`
(0003), LPM still enabled in the core after 0002 (0002 now turns it off),
unsolicited zero reports at bridge start and stop (removed), macro
modifiers landing in the same report as the key (they now lead and lag in
their own reports), and the D+ pull-up being present without VBUS
(`remaining-tells.md` §6).  Its remaining low items, `GET_IDLE` default 0
versus the recommended 500 ms and the exact host-side polling period, are
documented as deviations.

One more bus-level finding came out of checking the jitter refutation:
`f_hidg_write` queues every report with zero-length-packet termination, and
because the endpoint size equals the report length, every report is
followed by an empty packet on the next IN token.  No real HID device does
that, an analyser sees it on every keystroke, and it halves the achievable
report rate (one report per two polls).  Fixed in `kernel-patches/0001`.

The verifiers also corrected three citations and one characterisation in
the earlier text, applied in place above.  "What most firmware does" and
"we know of no host software that does this" (item 6) are general
knowledge, not verifiable from the sources.

## Offered follow-ups

None of these has been started.

* Kernel patch 0006 (bcdUSB 1.10 and 8-byte EP0 at full speed) for cloning
  USB 1.1 references (item 3).
* A clone mode for report descriptors and extra interfaces (item 4).
* An RP2040 USB front-end with a serial sink in the bridge (item 7), the
  option that retires the hardware tells wholesale.
```

## docs/macros.md

`6563 bytes, 128 lines, sha256 7824133cd153e6566ebc701e4ed136a20636d449c546a1da9f6d7d94c007c78f`

````markdown
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
````

## docs/troubleshooting.md

`7715 bytes, 160 lines, sha256 c5661f8818033dbdf45232eed8c32d68c6bbad4ce7dff7a1088cc668035a4edb`

````markdown
# Troubleshooting

Start with the three status commands and the journal:

```sh
hid-bridge check                 # config valid? descriptors? kernel features?
hid-bridge gadget status         # gadget bound? UDC state/speed?
hid-bridge ctl status            # bridge alive? sources attached? reports sent?
journalctl -u hid-gadget -u hid-bridge -b
```

## "no USB device controller found"

`/sys/class/udc` is empty.  The dwc2 controller is not in peripheral mode.

* `grep dwc2 /boot/firmware/config.txt` must show `dtoverlay=dwc2,dr_mode=peripheral`
  in a section that applies to the CM5 (`[all]` or `[cm5]`).  Reboot after editing.
* `lsmod | grep dwc2`; `sudo modprobe dwc2` if missing.
* `dmesg | grep -i dwc2` should mention the controller at `1000480000.usb`.
* Some carriers wire the dwc2 port only as host; then no gadget is possible on
  that board.

## Gadget bound, but UDC state never reaches "configured"

`state` stays at `not attached`, `powered` or `default`.

* `not attached`: no cable/host on the device port, or the cable is on a
  USB-A host port instead of the dwc2 port (`docs/hardware.md`).
* `default`/`addressed` for more than a second: the host stopped enumeration.
  Check `dmesg` on a Linux host or Device Manager on Windows for "device
  descriptor request failed".  Try another cable/port; try `max_speed =
  "high-speed"` temporarily to rule out a marginal full-speed link.
* Windows caches a bad enumeration under the same VID/PID/port.  Unplug,
  change the port or `product_id`, or delete the phantom device in Device
  Manager (View → Show hidden devices).

## Keys arrive on the CM5 console instead of the PC

The source is not grabbed (`grab_inputs = false`, the matching `[[inputs]]`
rule sets `grab = false`, or the grab failed; `hid-bridge ctl inputs` shows
`grabbed` per source).  Look
for "cannot grab" in the journal; another process (e.g. a desktop session)
holds the device.  Run Raspberry Pi OS **Lite** on the CM5 and keep
`grab_inputs = true`.

## Nothing typed on the PC, bridge says host_connected: false

`hid-bridge ctl status` → `keyboard.host_connected: false` means the last
write or read failed because the PC has not configured, or has
de-configured, the device (journal: `host not connected (...)`, `host
de-configured the interface; waiting for it to come back`).  See the UDC
section above.  Up to 16 key/button state changes are kept and sent when the
PC configures the device again (`host configured the interface again`,
`host connected again`); mouse motion is discarded; `dropped` counts the
failed attempts.  A flaky cable produces exactly this sequence of lines.

## `deferred` keeps rising, or `backing_off: true`, in `hid-bridge ctl status`

`deferred` counts writes that had to wait for the host's next poll; a fast
mouse stream makes it rise normally.  `backing_off: true` means the host has
suspended the bus (PC asleep, or the OS selectively suspended the keyboard)
and something was typed meanwhile: dwc2 refuses reports until the host
resumes, so the bridge retries after 50 ms, doubling up to 1 s (journal:
`host is not accepting reports (bus suspended?); retrying with backoff`,
then `host accepting reports again`), and waits 250 ms at a time without
trying while `udc.suspended` in `ctl status` reads 1.  Key state is kept for
the resume; motion made while the PC sleeps is discarded, as a real mouse's
would be.  A key press only wakes the PC with `kernel-patches/0004`
installed and `remote_wakeup = true`; wake it by other means otherwise.
`get_report_cache: false` (journal: `kernel lacks the f_hid GET_REPORT cache
ioctl`) means the kernel is older than 6.10 and answers `GET_REPORT` itself
after 2.5 s with zeros.

## A key seems stuck on the PC

First see who holds it: `hid-bridge ctl inputs` lists `keys_held` per source
as HID usage IDs (4 = A, 5 = B, ... 0xE0–0xE7 modifiers).  Then

```sh
hid-bridge ctl release-all
```

which clears every source's and macro's held keys and buttons.  Unplugging a
source always releases its keys.  A journal line `events dropped by the
kernel; state resynchronised (N keys held)` means the evdev buffer of that
device overflowed and the bridge rebuilt its held keys from the kernel;
harmless unless it repeats (the CM5 is starved of CPU).

## Mouse jumps or moves wrong in relative mode with PiKVM absolute pointer

Expected with absolute → relative conversion.  Set PiKVM to relative mode or
the bridge to `mouse.mode = "absolute"` (`docs/pikvm.md`).  Adjust
`abs_to_rel_resolution` to the PC's actual desktop size to get 1:1 motion.

## UEFI setup sees the keyboard but not the mouse

`mouse.mode` is `absolute`; firmware only understands boot-protocol relative
mice.  Switch to `relative`, then `systemctl restart hid-gadget hid-bridge`
and re-plug the PC side so it re-enumerates.

## Windows shows "Unknown USB Device (Device Descriptor Request Failed)"

Almost always cabling/port or a half-created gadget.  `sudo systemctl restart
hid-gadget hid-bridge`, replug, check `dmesg` on the CM5 for dwc2 errors.
(A manual `gadget down && gadget up` under a running bridge is tolerated:
the bridge notices the recreated `/dev/hidg*` nodes within one
`rescan_interval_ms` and reopens them, journal: `was recreated; reopening`.
Note that `hid-bridge gadget up` on an already bound gadget changes nothing;
descriptor changes need `gadget down` first, which the service restart does.)

## "UDC ... is busy"

Another gadget (e.g. a leftover `g_ether`/`g_serial` or a second configfs
gadget) owns the controller.  `ls /sys/kernel/config/usb_gadget/`, unbind it
(`echo "" > .../UDC`), remove `dtoverlay=dwc2` duplicates and `modules-load`
entries for `g_*` modules.

## PiKVM keyboard/mouse not listed by `hid-bridge inputs`

* Is the PiKVM's OTG cable in a CM5 **host** (USB-A) port?
* `lsusb` on the CM5 should show the PiKVM (`1d6b:0104` by default).
* `ls /dev/input/` should have new `event*` nodes when it is plugged in; if
  not, check `dmesg` for hid errors.
* Devices that expose neither ordinary keys nor a pointer (PiKVM's serial or
  Ethernet functions, for instance) are listed as ignored by design: a
  keyboard is any device with a key code below 0x100, a mouse any device
  with a left button or touch and an X axis.  `hid-bridge ctl inputs` shows
  the reason per ignored node; a node that cannot be opened is retried every
  5 s, and a node whose device changed (udev reuse) is re-evaluated.

## "cannot reach hid-bridge at /run/hid-bridge/ctl.sock"

The bridge is not running, `bridge.control_socket` was changed or emptied
(empty disables the socket), or the caller is not root (the socket is mode
0660, root).  `journalctl -u hid-bridge` shows `control socket unavailable`
if it could not be created at start-up.

## Latency

Full-speed HID polls both interfaces every 10 ms on a stock kernel (the
`poll_interval_ms` options only take effect on kernels with an f_hid
`interval` attribute), so the bridge adds at most one poll interval plus its
own processing, typically under 12 ms in total; `max_speed = "high-speed"`
polls every 1 ms.  On a stock kernel each report also occupies the
following poll slot with a zero-length packet, so a fast mouse stream is
limited to one report every 20 ms; `kernel-patches/0001` removes that.
If it feels slow, look for CPU hogs on the CM5 (`top`), and confirm the
PiKVM is not in absolute mode being converted to relative.

## Changing the descriptors

After editing `[gadget]`, `[keyboard]` or `[mouse]`:

```sh
sudo systemctl restart hid-gadget hid-bridge
```

Re-plug the PC side (or power-cycle the port) so the host reads the new
descriptors; Windows in particular caches descriptors per port until the
device disconnects.
````

## config/config.toml

`6013 bytes, 117 lines, sha256 37f4c0df3b44bceb691b508ef2ca59362cf4c9bb2652e75ad64f8c9c160f4757`

```toml
# hid-bridge configuration  (installed to /etc/hid-bridge/config.toml)
#
# Integers may be written in decimal or 0x hex.  Run `hid-bridge check` after
# editing to validate the file and print the descriptors the target will see.

[gadget]
# configfs directory name; no effect on the wire.
name = "hidbridge"

# USB vendor/product IDs presented to the target.  Windows and UEFI bind HID
# boot devices by class, never by these IDs, so any value works.  The default
# is the pid.codes "test" pair, explicitly reserved for private/lab use.  Set
# your own if you need a stable, unique hardware ID in Device Manager.
vendor_id = 0x1209
product_id = 0x0001
device_version = 0x0100   # bcdDevice

# String descriptors.  Set all three or none: once any string exists the kernel
# always allocates iManufacturer=1, iProduct=2, iSerialNumber=3 and answers an
# unset one with an empty string, which no real keyboard does.  install.sh
# fills `serial` with a random 12-digit hex value on first install.  Clearing
# all three gives a device with no strings at all (also common for cheap
# keyboards).
manufacturer = "Generic"
product = "USB Keyboard"
serial = ""

# Bus speed.  "full-speed" (12 Mbit/s) is what real keyboards and mice use and
# gives 10 ms polling (fixed by the kernel's HID function).  "high-speed" is a
# self-consistent USB 2.0 device with 1 ms polling, like a gaming keyboard.
# At full speed the controller still answers a DEVICE_QUALIFIER request (it is
# high-speed capable hardware); every OS and firmware tolerates that, and
# kernel-patches/0002 makes it STALL like a full-speed-only keyboard.
# "low-speed" is not usable with the CM5's controller.
max_speed = "full-speed"

# Configuration descriptor power attributes.
self_powered = false      # bmAttributes bit 6; false = looks bus powered like a real keyboard
remote_wakeup = true      # bmAttributes bit 5, as real keyboards advertise. A key press only wakes a
                          # sleeping PC with kernel-patches/0004 installed (stock dwc2 cannot signal
                          # remote wakeup). With false, a stock dwc2 still ACKs SET_FEATURE(REMOTE_WAKEUP);
                          # kernel-patches/0005 makes it STALL like a real device without the bit.
                          # true also enables f_hid wakeup_on_write on both interfaces when the
                          # kernel has it (0004), so keys and mouse activity wake the host.
max_power_ma = 100        # MaxPower, 1-500

# Force a specific UDC name (see /sys/class/udc); empty = the first one found.
udc = ""

[keyboard]
# "boot"     = the byte-exact HID 1.11 boot keyboard descriptor (usages 0x00-0x65).
# "extended" = same report format, key array widened to 0x00-0xFF so F13-F24 and
#              international keys are deliverable.  Both are boot-protocol compatible.
descriptor = "boot"
poll_interval_ms = 10     # bInterval, 1-255; Raspberry Pi kernels up to 6.12 have no f_hid 'interval'
                          # attribute and fix it at 10 ms (full speed) / 1 ms (high speed)

[mouse]
# "relative" = classic boot-protocol mouse + wheel (4-byte reports). Works in UEFI/BIOS.
# "absolute" = tablet-style absolute pointer 0..32767 (what PiKVM uses by default).
#              Not a boot mouse; needs an OS.  Set PiKVM to relative mode when using
#              "relative" here, or leave PiKVM absolute and let the bridge convert.
mode = "relative"
buttons = 3               # 3 or 5 (5 adds back/forward)
poll_interval_ms = 2      # same caveat as keyboard.poll_interval_ms
# Absolute source -> relative output: the source range is mapped onto this
# virtual screen size to produce pixel deltas.
abs_to_rel_resolution = [1920, 1080]
# Relative source -> absolute output: absolute units (0..32767) per count (positive number).
rel_to_abs_gain = 17.0

[bridge]
grab_inputs = true        # EVIOCGRAB every source so the CM5's own console never sees the keys
rescan_interval_ms = 1000 # hot-plug detection and host-state polling period
tap_ms = 30               # key/button hold time for macro taps and typing
step_ms = 20              # pause between macro steps, typed characters and repeated clicks
macro_jitter_ms = 30      # add 0..N ms of triangular (mode ~0.3 N) jitter to every macro hold, gap
                          # and modifier lead/lag so typed macros do not have a machine-like cadence
                          # (0 = off, must be >= 0)
forward_leds = true       # send Caps/Num/Scroll Lock state from the target back to the sources
control_socket = "/run/hid-bridge/ctl.sock"   # "" disables the control socket
log_level = "info"        # debug | info | warning | error

# ---------------------------------------------------------------------------
# Input rules: evaluated top to bottom, first match wins, default is
# pass-through for every keyboard/mouse.  Match on any subset of
#   name    regex against the evdev device name   (hid-bridge inputs)
#   phys    regex against the physical USB path   (e.g. "usb-xhci-hcd\\.0-1/")
#   vendor / product   USB IDs
# role: passthrough | macro | ignore
# label: free text shown in logs and status;  grab: true|false overrides bridge.grab_inputs
#
# Example: a macro keypad whose keys launch macros instead of being forwarded.
# [[inputs]]
# label = "stream deck knock-off"
# vendor = 0x1a2c
# product = 0x2d43
# role = "macro"
# unbound = "drop"        # keys without a binding: drop | passthrough
# [inputs.bindings]
# KEY_1 = "ctrl_alt_del"
# KEY_2 = "win_lock"
# KEY_3 = "sim_pause"
#
# Example: never forward the keyboard you use to administer the CM5 itself.
# [[inputs]]
# name = "^Dell KB216"
# role = "ignore"

# ---------------------------------------------------------------------------
# Macros: name = [steps] (or a single step string).  See docs/macros.md for the step language.
[macros]
ctrl_alt_del = ["ctrl+alt+delete"]
win_lock = ["win+l"]
task_manager = ["ctrl+shift+esc"]
sim_pause = ["pause"]
example_login = ["ctrl+alt+delete", "wait 1200", "type CHANGE-ME", "enter"]
```

## hid_bridge/__init__.py

`346 bytes, 9 lines, sha256 955d5ef674dd015c30e0875e74ca2c0de9ef011bea59f6cfabc22f5d27a69d23`

```python
"""hid-bridge: a Raspberry Pi CM5 USB-gadget HID bridge.

The CM5 enumerates on its USB device port as a plain full-speed USB HID
keyboard + mouse (boot-protocol, no vendor extensions, no composite
class markers) and re-transmits input received from a PiKVM and from
local macro devices attached to its USB host ports.
"""

__version__ = "0.1.0"
```

## hid_bridge/__main__.py

`10929 bytes, 242 lines, sha256 9e5d920a6d5cce1797848ae8147a1252c8f9338607954bc9dee6e4fd5a8e0bb1`

```python
"""Command line entry point: ``python3 -m hid_bridge <command>``."""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from . import __version__
from .config import ConfigError, load_config
from .descriptors import report_bit_sizes


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _hexdump(data: bytes, width: int = 16) -> str:
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        lines.append("  " + " ".join(f"{b:02x}" for b in chunk))
    return "\n".join(lines)


def cmd_gadget(args, cfg) -> int:
    from .gadget import Gadget, GadgetError
    gadget = Gadget(cfg)
    try:
        if args.action == "up":
            devices = gadget.up()
            print(json.dumps(devices, indent=2))
            for warning in gadget.warnings:
                print(f"warning: {warning}", file=sys.stderr)
        elif args.action == "down":
            gadget.down()
        elif args.action == "status":
            print(json.dumps(gadget.status(), indent=2))
    except GadgetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_run(args, cfg) -> int:
    from .bridge import Bridge
    from .gadget import Gadget, GadgetError, load_state
    devices = load_state()
    if devices is None or not all(os.path.exists(devices.get(k, "")) for k in ("keyboard", "mouse")):
        gadget = Gadget(cfg)
        try:
            if gadget.exists() and gadget.bound_udc():
                devices = gadget.resolve_devices()
            elif args.auto_gadget:
                devices = gadget.up()
            else:
                print("error: gadget is not up; run 'hid-bridge gadget up' first (or use --auto-gadget)", file=sys.stderr)
                return 1
        except GadgetError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    Bridge(cfg, devices).run()
    return 0


def cmd_inputs(args, cfg) -> int:
    from .linux_input import InputDevice, list_event_nodes
    rows = []
    for path in list_event_nodes():
        try:
            dev = InputDevice(path)
        except OSError as exc:
            rows.append((path, f"<cannot open: {exc.strerror}>", "", "", ""))
            continue
        try:
            ident = dev.identity
            rule = cfg.rule_for(ident.name, ident.phys, ident.vendor, ident.product)
            kinds = []
            if dev.is_keyboard:
                kinds.append("keyboard")
            if dev.is_mouse:
                kinds.append("mouse(abs)" if dev.has_abs_pointer else "mouse")
            role = rule.role if kinds else "ignored (not kbd/mouse)"
            rows.append((path, ident.name, f"{ident.vendor:04x}:{ident.product:04x}", ",".join(kinds) or "-", f"{role} [{rule.describe()}]"))
        finally:
            dev.close()
    if not rows:
        print("no /dev/input/event* devices found")
        return 0
    widths = [max(len(str(r[i])) for r in rows + [("PATH", "NAME", "ID", "KIND", "ROLE")]) for i in range(5)]
    header = ("PATH", "NAME", "ID", "KIND", "ROLE")
    for row in [header] + rows:
        print("  ".join(str(col).ljust(widths[i]) for i, col in enumerate(row)).rstrip())
    return 0


def cmd_check(args, cfg) -> int:
    from .descriptors import KEYBOARD_REPORT_LENGTH, keyboard_report_descriptor, mouse_report_descriptor, mouse_report_length
    from .gadget import Gadget, list_udcs

    ok = True
    print(f"config: {cfg.path or '(defaults)'}")
    g = cfg.gadget
    print(f"device: idVendor=0x{g.vendor_id:04x} idProduct=0x{g.product_id:04x} bcdDevice=0x{g.device_version:04x} "
          f"max_speed={g.max_speed} strings={'/'.join(filter(None, (g.manufacturer, g.product, g.serial))) or '(none)'}")
    attrs = 0x80 | (0x40 if g.self_powered else 0) | (0x20 if g.remote_wakeup else 0)
    print(f"config: bmAttributes=0x{attrs:02x} MaxPower={g.max_power_ma}mA, 2 interfaces (HID keyboard, HID mouse)")
    if (g.vendor_id, g.product_id) == (0x1209, 0x0001):
        print("  note: 0x1209:0x0001 is the pid.codes *test* ID; USB ID databases (lsusb, USBView) label it as such."
              " Choose your own IDs in [gadget] if the device must not read as a test/hobby device")
    strings_set = [bool(g.manufacturer), bool(g.product), bool(g.serial)]
    if any(strings_set) and not all(strings_set):
        print("  note: set all of manufacturer/product/serial or none; an unset one becomes an empty string descriptor"
              " (install.sh fills in a random serial on first install)")
    print("kernel-fixed on a stock kernel: bcdUSB 0x0200 (0x0201 + BOS when the controller enables LPM), "
          "bMaxPacketSize0 64, bcdHID 1.01, bInterval 10 ms at full speed / 1 ms at high speed")
    print("with kernel-patches/ installed: bcdHID 1.10, bcdUSB 0x0200 without BOS at full speed, GET_IDLE 0, "
          "no interface string, no ZLP after reports, report-type checks, remote wakeup, real-device answers to "
          "GET_STATUS/SET_FEATURE; bMaxPacketSize0 and bInterval unchanged")

    kbd = keyboard_report_descriptor(cfg.keyboard.descriptor == "extended")
    in_bits, out_bits = report_bit_sizes(kbd)
    print(f"\nkeyboard descriptor ({cfg.keyboard.descriptor}, {len(kbd)} bytes): input {in_bits // 8} bytes, output {out_bits // 8} byte(s)")
    print(_hexdump(kbd))
    if in_bits != KEYBOARD_REPORT_LENGTH * 8:
        print("  ERROR: keyboard report length mismatch")
        ok = False

    mouse = mouse_report_descriptor(cfg.mouse.mode, cfg.mouse.buttons)
    in_bits, out_bits = report_bit_sizes(mouse)
    print(f"\nmouse descriptor ({cfg.mouse.mode}, {cfg.mouse.buttons} buttons, {len(mouse)} bytes): input {in_bits // 8} bytes")
    print(_hexdump(mouse))
    if in_bits != mouse_report_length(cfg.mouse.mode) * 8:
        print("  ERROR: mouse report length mismatch")
        ok = False

    print(f"\nmacros defined: {', '.join(sorted(cfg.macros)) or '(none)'}")
    print(f"input rules: {len(cfg.inputs)}")
    for i, rule in enumerate(cfg.inputs):
        print(f"  [{i}] {rule.describe()} -> {rule.role}" + (f", {len(rule.bindings)} binding(s)" if rule.bindings else ""))

    print("\nkernel / platform:")
    udcs = list_udcs()
    print(f"  UDCs: {', '.join(udcs) if udcs else 'none (dwc2 overlay missing or not in peripheral mode?)'}")
    print(f"  configfs usb_gadget: {'present' if os.path.isdir(g.configfs) else 'missing (modprobe libcomposite)'}")
    for candidate in ("/boot/firmware/config.txt", "/boot/config.txt"):
        if os.path.exists(candidate):
            try:
                with open(candidate) as fh:
                    text = fh.read()
            except OSError:
                text = ""
            has = any(line.strip().startswith("dtoverlay=dwc2") for line in text.splitlines())
            print(f"  {candidate}: dwc2 overlay {'configured' if has else 'NOT configured'}")
            break
    gadget = Gadget(cfg)
    if gadget.exists():
        st = gadget.status()
        print(f"  gadget {g.name}: {'bound to ' + st['udc']['udc'] + ', host state ' + st['udc']['state'] + ', speed ' + st['udc']['current_speed'] if st.get('bound') else 'present, unbound'}")
        print(f"  kernel-patches/ present: {'yes (strict_report_types attribute found)' if st.get('patched_kernel') else 'no'}")
        if st.get("bound"):
            print(f"  controller LPM: {st['udc']['lpm']} -> device descriptor bcdUSB on the wire: {st['udc']['bcdUSB_on_wire']}")
        for role, func in st.get("functions", {}).items():
            missing = [k for k in ("no_out_endpoint", "strict_report_types", "wakeup_on_write", "interval") if func.get(k) == "n/a"]
            if missing:
                print(f"  {role}: kernel lacks optional f_hid attribute(s): {', '.join(missing)}")
    else:
        print(f"  gadget {g.name}: not created")
    print("\nOK" if ok else "\nPROBLEMS FOUND")
    return 0 if ok else 1


def cmd_ctl(args, cfg) -> int:
    from .control import send_request
    if args.what == "status":
        request = {"cmd": "status"}
    elif args.what == "inputs":
        request = {"cmd": "inputs"}
    elif args.what == "macro":
        request = {"cmd": "macro", "name": args.value[0] if args.value else ""}
    elif args.what == "type":
        request = {"cmd": "type", "text": " ".join(args.value)}
    elif args.what == "keys":
        request = {"cmd": "keys", "combo": " ".join(args.value)}
    elif args.what == "steps":
        request = {"cmd": "steps", "steps": args.value}
    elif args.what == "release-all":
        request = {"cmd": "release_all"}
    else:  # pragma: no cover
        raise SystemExit(f"unknown ctl command {args.what}")
    try:
        reply = send_request(cfg.bridge.control_socket, request)
    except (OSError, ConnectionError) as exc:
        print(f"error: cannot reach hid-bridge at {cfg.bridge.control_socket}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(reply, indent=2))
    return 0 if reply.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hid-bridge", description="CM5 USB HID keyboard/mouse bridge")
    parser.add_argument("-c", "--config", help="config file (default: $HID_BRIDGE_CONFIG or /etc/hid-bridge/config.toml)")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    parser.add_argument("--version", action="version", version=f"hid-bridge {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("gadget", help="create/remove/inspect the USB gadget")
    p.add_argument("action", choices=("up", "down", "status"))
    p.set_defaults(func=cmd_gadget)

    p = sub.add_parser("run", help="run the bridge daemon")
    p.add_argument("--auto-gadget", action="store_true", help="bring the gadget up if it is not")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("inputs", help="list input devices and how they would be handled")
    p.set_defaults(func=cmd_inputs)

    p = sub.add_parser("check", help="validate the configuration and show what the host will see")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("ctl", help="talk to the running bridge")
    p.add_argument("what", choices=("status", "inputs", "macro", "type", "keys", "steps", "release-all"))
    p.add_argument("value", nargs="*")
    p.set_defaults(func=cmd_ctl)

    args = parser.parse_args(argv)
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    _setup_logging("debug" if args.verbose else cfg.bridge.log_level)
    return args.func(args, cfg)


if __name__ == "__main__":
    sys.exit(main())
```

## hid_bridge/config.py

`10590 bytes, 259 lines, sha256 a16c6c755a98ef4343728d8e902cc077d25061711b77aa54c64736ce95fe9a00`

```python
"""Configuration loading (TOML, standard library ``tomllib``)."""
from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from typing import Any

DEFAULT_CONFIG_PATH = "/etc/hid-bridge/config.toml"


class ConfigError(Exception):
    pass


@dataclass
class GadgetConfig:
    name: str = "hidbridge"
    vendor_id: int = 0x1209
    product_id: int = 0x0001
    device_version: int = 0x0100
    manufacturer: str = "Generic"
    product: str = "USB Keyboard"
    serial: str = ""
    max_speed: str = "full-speed"
    self_powered: bool = False
    remote_wakeup: bool = True
    max_power_ma: int = 100
    udc: str = ""
    configfs: str = "/sys/kernel/config/usb_gadget"


@dataclass
class KeyboardConfig:
    descriptor: str = "boot"  # boot | extended
    poll_interval_ms: int = 10


@dataclass
class MouseConfig:
    mode: str = "relative"  # relative | absolute
    buttons: int = 3
    poll_interval_ms: int = 2
    # Used when converting an absolute source (PiKVM absolute mode) to relative
    # output: the source range is mapped onto this many "pixels".
    abs_to_rel_resolution: tuple[int, int] = (1920, 1080)
    # Used when converting a relative source to absolute output: how many
    # absolute units (0..32767) one relative count moves the virtual cursor.
    rel_to_abs_gain: float = 17.0


@dataclass
class BridgeConfig:
    grab_inputs: bool = True
    rescan_interval_ms: int = 1000
    tap_ms: int = 30
    step_ms: int = 20
    macro_jitter_ms: int = 30
    forward_leds: bool = True
    control_socket: str = "/run/hid-bridge/ctl.sock"
    log_level: str = "info"


@dataclass
class InputRule:
    name: str | None = None      # regex matched against the evdev device name
    phys: str | None = None      # regex matched against the physical path
    vendor: int | None = None
    product: int | None = None
    role: str = "passthrough"    # passthrough | macro | ignore
    grab: bool | None = None     # None -> bridge.grab_inputs
    unbound: str = "drop"        # for role=macro: drop | passthrough
    bindings: dict[str, str] = field(default_factory=dict)
    label: str = ""

    def matches(self, name: str, phys: str, vendor: int, product: int) -> bool:
        if self.name is not None and not re.search(self.name, name):
            return False
        if self.phys is not None and not re.search(self.phys, phys):
            return False
        if self.vendor is not None and self.vendor != vendor:
            return False
        if self.product is not None and self.product != product:
            return False
        return True

    def describe(self) -> str:
        if self.label:
            return self.label
        parts = []
        if self.name is not None:
            parts.append(f"name~{self.name!r}")
        if self.phys is not None:
            parts.append(f"phys~{self.phys!r}")
        if self.vendor is not None:
            parts.append(f"vendor={self.vendor:04x}")
        if self.product is not None:
            parts.append(f"product={self.product:04x}")
        return " ".join(parts) or "<any>"


@dataclass
class Config:
    gadget: GadgetConfig = field(default_factory=GadgetConfig)
    keyboard: KeyboardConfig = field(default_factory=KeyboardConfig)
    mouse: MouseConfig = field(default_factory=MouseConfig)
    bridge: BridgeConfig = field(default_factory=BridgeConfig)
    inputs: list[InputRule] = field(default_factory=list)
    macros: dict[str, list[str]] = field(default_factory=dict)
    path: str = ""

    def rule_for(self, name: str, phys: str, vendor: int, product: int) -> InputRule:
        for rule in self.inputs:
            if rule.matches(name, phys, vendor, product):
                return rule
        return InputRule(label="default passthrough")


def _int(value: Any, what: str) -> int:
    if isinstance(value, bool):
        raise ConfigError(f"{what}: expected an integer, got a boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    raise ConfigError(f"{what}: expected an integer (decimal or 0x hex), got {value!r}")


def _apply(section: dict[str, Any], target: Any, what: str, int_fields: set[str]) -> None:
    for key, value in section.items():
        if not hasattr(target, key):
            raise ConfigError(f"{what}: unknown option {key!r}")
        if key in int_fields:
            value = _int(value, f"{what}.{key}")
        setattr(target, key, value)


def parse_config(data: dict[str, Any], path: str = "") -> Config:
    cfg = Config(path=path)
    known = {"gadget", "keyboard", "mouse", "bridge", "inputs", "macros"}
    unknown = set(data) - known
    if unknown:
        raise ConfigError(f"unknown top-level section(s): {', '.join(sorted(unknown))}")

    _apply(data.get("gadget", {}), cfg.gadget, "gadget",
           {"vendor_id", "product_id", "device_version", "max_power_ma"})
    _apply(data.get("keyboard", {}), cfg.keyboard, "keyboard", {"poll_interval_ms"})
    mouse = dict(data.get("mouse", {}))
    if "abs_to_rel_resolution" in mouse:
        res = mouse.pop("abs_to_rel_resolution")
        if not (isinstance(res, list) and len(res) == 2):
            raise ConfigError("mouse.abs_to_rel_resolution must be [width, height]")
        cfg.mouse.abs_to_rel_resolution = (_int(res[0], "width"), _int(res[1], "height"))
    _apply(mouse, cfg.mouse, "mouse", {"buttons", "poll_interval_ms"})
    _apply(data.get("bridge", {}), cfg.bridge, "bridge",
           {"rescan_interval_ms", "tap_ms", "step_ms", "macro_jitter_ms"})

    for index, raw in enumerate(data.get("inputs", [])):
        if not isinstance(raw, dict):
            raise ConfigError(f"inputs[{index}] must be a table")
        rule = InputRule()
        for key, value in raw.items():
            if key in ("vendor", "product"):
                setattr(rule, key, _int(value, f"inputs[{index}].{key}"))
            elif key == "bindings":
                if not isinstance(value, dict):
                    raise ConfigError(f"inputs[{index}].bindings must be a table")
                rule.bindings = {str(k).upper(): str(v) for k, v in value.items()}
            elif hasattr(rule, key):
                setattr(rule, key, value)
            else:
                raise ConfigError(f"inputs[{index}]: unknown option {key!r}")
        if rule.role not in ("passthrough", "macro", "ignore"):
            raise ConfigError(f"inputs[{index}].role must be passthrough, macro or ignore")
        if rule.unbound not in ("drop", "passthrough"):
            raise ConfigError(f"inputs[{index}].unbound must be drop or passthrough")
        for pattern_key in ("name", "phys"):
            pattern = getattr(rule, pattern_key)
            if pattern is not None:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    raise ConfigError(f"inputs[{index}].{pattern_key}: bad regex: {exc}") from exc
        cfg.inputs.append(rule)

    macros = data.get("macros", {})
    if not isinstance(macros, dict):
        raise ConfigError("macros must be a table of name = [steps]")
    for name, steps in macros.items():
        if isinstance(steps, str):
            steps = [steps]
        if not isinstance(steps, list) or not all(isinstance(s, str) for s in steps):
            raise ConfigError(f"macros.{name} must be a string or an array of step strings")
        cfg.macros[str(name)] = list(steps)

    validate(cfg)
    return cfg


def validate(cfg: Config) -> None:
    g = cfg.gadget
    for label, value in (("vendor_id", g.vendor_id), ("product_id", g.product_id),
                         ("device_version", g.device_version)):
        if not 0 <= value <= 0xFFFF:
            raise ConfigError(f"gadget.{label} must be within 0x0000-0xFFFF")
    if g.max_speed not in ("low-speed", "full-speed", "high-speed"):
        raise ConfigError("gadget.max_speed must be low-speed, full-speed or high-speed")
    if not 0 < g.max_power_ma <= 500:
        raise ConfigError("gadget.max_power_ma must be within 1-500")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", g.name):
        raise ConfigError("gadget.name may only contain letters, digits, '_', '.' and '-'")
    if cfg.keyboard.descriptor not in ("boot", "extended"):
        raise ConfigError("keyboard.descriptor must be boot or extended")
    if cfg.mouse.mode not in ("relative", "absolute"):
        raise ConfigError("mouse.mode must be relative or absolute")
    if cfg.mouse.buttons not in (3, 5):
        raise ConfigError("mouse.buttons must be 3 or 5")
    for label, value in (("keyboard.poll_interval_ms", cfg.keyboard.poll_interval_ms),
                         ("mouse.poll_interval_ms", cfg.mouse.poll_interval_ms)):
        if not 1 <= value <= 255:
            raise ConfigError(f"{label} must be within 1-255")
    gain = cfg.mouse.rel_to_abs_gain
    if isinstance(gain, bool) or not isinstance(gain, (int, float)) or gain <= 0:
        raise ConfigError("mouse.rel_to_abs_gain must be a positive number")
    if cfg.bridge.macro_jitter_ms < 0:
        raise ConfigError("bridge.macro_jitter_ms must be >= 0")
    if cfg.bridge.log_level.upper() not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        raise ConfigError("bridge.log_level must be debug, info, warning or error")
    from .keymap import KEY_CODES
    for rule in cfg.inputs:
        for key, macro in rule.bindings.items():
            if key not in KEY_CODES:
                raise ConfigError(f"binding {key}: unknown evdev key name (see hid_bridge/keymap.py)")
            if macro not in cfg.macros:
                raise ConfigError(f"binding {key} -> {macro!r}: no such macro")
    # Validate macro step syntax early so a typo fails at start-up, not mid-run.
    from . import macros as macro_module
    for name, steps in cfg.macros.items():
        for step in steps:
            try:
                macro_module.parse_step(step, cfg.macros)
            except macro_module.MacroError as exc:
                raise ConfigError(f"macros.{name}: {exc}") from exc


def load_config(path: str | None = None) -> Config:
    path = path or os.environ.get("HID_BRIDGE_CONFIG", DEFAULT_CONFIG_PATH)
    try:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    except FileNotFoundError:
        raise ConfigError(f"config file not found: {path}")
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: {exc}")
    return parse_config(data, path)
```

## hid_bridge/descriptors.py

`7843 bytes, 195 lines, sha256 5739f05ce5af52aec032d4150350729fd5db49136a0ca31d1506c00e6a72f404`

```python
"""USB HID report descriptors presented to the target computer.

The keyboard descriptor is the canonical boot-protocol keyboard descriptor
from the USB HID 1.11 specification (Appendix E.6), byte for byte.  The
relative mouse descriptor is the boot-protocol mouse (Appendix E.10) with the
ubiquitous wheel byte appended; the first three report bytes are exactly the
boot mouse format, so the device stays usable when a BIOS/UEFI switches it to
boot protocol with SET_PROTOCOL.
"""
from __future__ import annotations

KEYBOARD_REPORT_LENGTH = 8
KEYBOARD_OUTPUT_LENGTH = 1  # LED report


def keyboard_report_descriptor(extended: bool = False) -> bytes:
    """Return the keyboard report descriptor.

    ``extended=False`` is the exact 63-byte HID spec boot keyboard descriptor
    (array usages 0x00-0x65).  ``extended=True`` widens the key array to
    0x00-0xFF so that F13-F24, international and keypad-extra keys can be
    delivered; the report format is unchanged and still boot compatible.
    """
    if extended:
        key_array = bytes([
            0x95, 0x06,        # Report Count (6)
            0x75, 0x08,        # Report Size (8)
            0x15, 0x00,        # Logical Minimum (0)
            0x26, 0xFF, 0x00,  # Logical Maximum (255)
            0x05, 0x07,        # Usage Page (Key Codes)
            0x19, 0x00,        # Usage Minimum (0)
            0x2A, 0xFF, 0x00,  # Usage Maximum (255)
            0x81, 0x00,        # Input (Data, Array)
        ])
    else:
        key_array = bytes([
            0x95, 0x06,  # Report Count (6)
            0x75, 0x08,  # Report Size (8)
            0x15, 0x00,  # Logical Minimum (0)
            0x25, 0x65,  # Logical Maximum (101)
            0x05, 0x07,  # Usage Page (Key Codes)
            0x19, 0x00,  # Usage Minimum (0)
            0x29, 0x65,  # Usage Maximum (101)
            0x81, 0x00,  # Input (Data, Array)
        ])
    return bytes([
        0x05, 0x01,  # Usage Page (Generic Desktop)
        0x09, 0x06,  # Usage (Keyboard)
        0xA1, 0x01,  # Collection (Application)
        0x05, 0x07,  #   Usage Page (Key Codes)
        0x19, 0xE0,  #   Usage Minimum (224)
        0x29, 0xE7,  #   Usage Maximum (231)
        0x15, 0x00,  #   Logical Minimum (0)
        0x25, 0x01,  #   Logical Maximum (1)
        0x75, 0x01,  #   Report Size (1)
        0x95, 0x08,  #   Report Count (8)
        0x81, 0x02,  #   Input (Data, Variable, Absolute)  ; modifier byte
        0x95, 0x01,  #   Report Count (1)
        0x75, 0x08,  #   Report Size (8)
        0x81, 0x01,  #   Input (Constant)                   ; reserved byte
        0x95, 0x05,  #   Report Count (5)
        0x75, 0x01,  #   Report Size (1)
        0x05, 0x08,  #   Usage Page (LEDs)
        0x19, 0x01,  #   Usage Minimum (1)
        0x29, 0x05,  #   Usage Maximum (5)
        0x91, 0x02,  #   Output (Data, Variable, Absolute) ; LED report
        0x95, 0x01,  #   Report Count (1)
        0x75, 0x03,  #   Report Size (3)
        0x91, 0x01,  #   Output (Constant)                  ; LED padding
    ]) + key_array + bytes([
        0xC0,        # End Collection
    ])


def mouse_report_descriptor(mode: str = "relative", buttons: int = 3) -> bytes:
    """Return the mouse report descriptor for ``mode`` ("relative"/"absolute")."""
    if buttons not in (3, 5):
        raise ValueError("mouse buttons must be 3 or 5")
    padding_bits = 8 - buttons
    header = bytes([
        0x05, 0x01,           # Usage Page (Generic Desktop)
        0x09, 0x02,           # Usage (Mouse)
        0xA1, 0x01,           # Collection (Application)
        0x09, 0x01,           #   Usage (Pointer)
        0xA1, 0x00,           #   Collection (Physical)
        0x05, 0x09,           #     Usage Page (Buttons)
        0x19, 0x01,           #     Usage Minimum (1)
        0x29, buttons,        #     Usage Maximum (n)
        0x15, 0x00,           #     Logical Minimum (0)
        0x25, 0x01,           #     Logical Maximum (1)
        0x95, buttons,        #     Report Count (n)
        0x75, 0x01,           #     Report Size (1)
        0x81, 0x02,           #     Input (Data, Variable, Absolute) ; buttons
        0x95, 0x01,           #     Report Count (1)
        0x75, padding_bits,   #     Report Size (8-n)
        0x81, 0x01,           #     Input (Constant)                 ; padding
        0x05, 0x01,           #     Usage Page (Generic Desktop)
    ])
    if mode == "relative":
        axes = bytes([
            0x09, 0x30,  #     Usage (X)
            0x09, 0x31,  #     Usage (Y)
            0x09, 0x38,  #     Usage (Wheel)
            0x15, 0x81,  #     Logical Minimum (-127)
            0x25, 0x7F,  #     Logical Maximum (127)
            0x75, 0x08,  #     Report Size (8)
            0x95, 0x03,  #     Report Count (3)
            0x81, 0x06,  #     Input (Data, Variable, Relative)
        ])
    elif mode == "absolute":
        axes = bytes([
            0x09, 0x30,        #     Usage (X)
            0x09, 0x31,        #     Usage (Y)
            0x15, 0x00,        #     Logical Minimum (0)
            0x26, 0xFF, 0x7F,  #     Logical Maximum (32767)
            0x75, 0x10,        #     Report Size (16)
            0x95, 0x02,        #     Report Count (2)
            0x81, 0x02,        #     Input (Data, Variable, Absolute)
            0x09, 0x38,        #     Usage (Wheel)
            0x15, 0x81,        #     Logical Minimum (-127)
            0x25, 0x7F,        #     Logical Maximum (127)
            0x75, 0x08,        #     Report Size (8)
            0x95, 0x01,        #     Report Count (1)
            0x81, 0x06,        #     Input (Data, Variable, Relative)
        ])
    else:
        raise ValueError(f"unknown mouse mode {mode!r}")
    return header + axes + bytes([
        0xC0,  #   End Collection
        0xC0,  # End Collection
    ])


def mouse_report_length(mode: str) -> int:
    if mode == "relative":
        return 4  # buttons, x, y, wheel
    if mode == "absolute":
        return 6  # buttons, x(16), y(16), wheel
    raise ValueError(f"unknown mouse mode {mode!r}")


ABS_MAX_VALUE = 0x7FFF

# HID interface subclass/protocol constants
HID_SUBCLASS_NONE = 0
HID_SUBCLASS_BOOT = 1
HID_PROTOCOL_NONE = 0
HID_PROTOCOL_KEYBOARD = 1
HID_PROTOCOL_MOUSE = 2


def report_bit_sizes(descriptor: bytes) -> tuple[int, int]:
    """Parse a report descriptor and return (input_bits, output_bits).

    A tiny short-item parser used by the tests and by ``hid-bridge check`` to
    prove that the declared report lengths match what the descriptor encodes.
    Report IDs are deliberately unsupported: a generic keyboard uses none.
    """
    input_bits = 0
    output_bits = 0
    report_size = 0
    report_count = 0
    i = 0
    depth = 0
    while i < len(descriptor):
        prefix = descriptor[i]
        i += 1
        if prefix == 0xFE:
            raise ValueError("long items are not supported")
        size = prefix & 0x03
        if size == 3:
            size = 4
        item_type = (prefix >> 2) & 0x03
        tag = prefix >> 4
        data = int.from_bytes(descriptor[i:i + size], "little") if size else 0
        i += size
        if item_type == 0:  # main
            if tag == 0x8:
                input_bits += report_size * report_count
            elif tag == 0x9:
                output_bits += report_size * report_count
            elif tag == 0xA:
                depth += 1
            elif tag == 0xC:
                depth -= 1
        elif item_type == 1:  # global
            if tag == 0x7:
                report_size = data
            elif tag == 0x9:
                report_count = data
            elif tag == 0x8:
                raise ValueError("report IDs are not used by this project")
    if depth != 0:
        raise ValueError("unbalanced collections")
    return input_bits, output_bits
```

## hid_bridge/keymap.py

`13465 bytes, 227 lines, sha256 4fb5629c88e9830bbd696073d700b98ed0eb2c4a86e6ba551c7a02ab9c8a777f`

```python
"""Key code tables.

* ``KEY_CODES``      evdev key names -> evdev codes (<linux/input-event-codes.h>)
* ``EVDEV_TO_HID``   evdev key codes -> USB HID Keyboard/Keypad page usage IDs
* ``KEY_ALIASES``    friendly names used in macro definitions -> HID usage IDs
* ``US_LAYOUT``      printable characters -> (usage, needs_shift) for ``type``

``EVDEV_TO_HID`` is the inverse of the ``hid_keyboard[]`` table in the Linux
kernel's ``drivers/hid/hid-input.c`` restricted to usages a plain boot
protocol keyboard emits (0x04-0xA4 plus the 0xE0-0xE7 modifiers).
"""
from __future__ import annotations

KEY_CODES: dict[str, int] = {
    "KEY_ESC": 1, "KEY_1": 2, "KEY_2": 3, "KEY_3": 4, "KEY_4": 5, "KEY_5": 6,
    "KEY_6": 7, "KEY_7": 8, "KEY_8": 9, "KEY_9": 10, "KEY_0": 11,
    "KEY_MINUS": 12, "KEY_EQUAL": 13, "KEY_BACKSPACE": 14, "KEY_TAB": 15,
    "KEY_Q": 16, "KEY_W": 17, "KEY_E": 18, "KEY_R": 19, "KEY_T": 20, "KEY_Y": 21,
    "KEY_U": 22, "KEY_I": 23, "KEY_O": 24, "KEY_P": 25,
    "KEY_LEFTBRACE": 26, "KEY_RIGHTBRACE": 27, "KEY_ENTER": 28, "KEY_LEFTCTRL": 29,
    "KEY_A": 30, "KEY_S": 31, "KEY_D": 32, "KEY_F": 33, "KEY_G": 34, "KEY_H": 35,
    "KEY_J": 36, "KEY_K": 37, "KEY_L": 38,
    "KEY_SEMICOLON": 39, "KEY_APOSTROPHE": 40, "KEY_GRAVE": 41, "KEY_LEFTSHIFT": 42,
    "KEY_BACKSLASH": 43,
    "KEY_Z": 44, "KEY_X": 45, "KEY_C": 46, "KEY_V": 47, "KEY_B": 48, "KEY_N": 49, "KEY_M": 50,
    "KEY_COMMA": 51, "KEY_DOT": 52, "KEY_SLASH": 53, "KEY_RIGHTSHIFT": 54,
    "KEY_KPASTERISK": 55, "KEY_LEFTALT": 56, "KEY_SPACE": 57, "KEY_CAPSLOCK": 58,
    "KEY_F1": 59, "KEY_F2": 60, "KEY_F3": 61, "KEY_F4": 62, "KEY_F5": 63, "KEY_F6": 64,
    "KEY_F7": 65, "KEY_F8": 66, "KEY_F9": 67, "KEY_F10": 68,
    "KEY_NUMLOCK": 69, "KEY_SCROLLLOCK": 70,
    "KEY_KP7": 71, "KEY_KP8": 72, "KEY_KP9": 73, "KEY_KPMINUS": 74,
    "KEY_KP4": 75, "KEY_KP5": 76, "KEY_KP6": 77, "KEY_KPPLUS": 78,
    "KEY_KP1": 79, "KEY_KP2": 80, "KEY_KP3": 81, "KEY_KP0": 82, "KEY_KPDOT": 83,
    "KEY_ZENKAKUHANKAKU": 85, "KEY_102ND": 86, "KEY_F11": 87, "KEY_F12": 88,
    "KEY_RO": 89, "KEY_KATAKANA": 90, "KEY_HIRAGANA": 91, "KEY_HENKAN": 92,
    "KEY_KATAKANAHIRAGANA": 93, "KEY_MUHENKAN": 94, "KEY_KPJPCOMMA": 95,
    "KEY_KPENTER": 96, "KEY_RIGHTCTRL": 97, "KEY_KPSLASH": 98, "KEY_SYSRQ": 99,
    "KEY_RIGHTALT": 100, "KEY_LINEFEED": 101,
    "KEY_HOME": 102, "KEY_UP": 103, "KEY_PAGEUP": 104, "KEY_LEFT": 105, "KEY_RIGHT": 106,
    "KEY_END": 107, "KEY_DOWN": 108, "KEY_PAGEDOWN": 109, "KEY_INSERT": 110, "KEY_DELETE": 111,
    "KEY_MACRO": 112, "KEY_MUTE": 113, "KEY_VOLUMEDOWN": 114, "KEY_VOLUMEUP": 115,
    "KEY_POWER": 116, "KEY_KPEQUAL": 117, "KEY_KPPLUSMINUS": 118, "KEY_PAUSE": 119,
    "KEY_SCALE": 120, "KEY_KPCOMMA": 121, "KEY_HANGEUL": 122, "KEY_HANJA": 123,
    "KEY_YEN": 124, "KEY_LEFTMETA": 125, "KEY_RIGHTMETA": 126, "KEY_COMPOSE": 127,
    "KEY_STOP": 128, "KEY_AGAIN": 129, "KEY_PROPS": 130, "KEY_UNDO": 131, "KEY_FRONT": 132,
    "KEY_COPY": 133, "KEY_OPEN": 134, "KEY_PASTE": 135, "KEY_FIND": 136, "KEY_CUT": 137,
    "KEY_HELP": 138, "KEY_MENU": 139, "KEY_CALC": 140, "KEY_SETUP": 141, "KEY_SLEEP": 142,
    "KEY_WAKEUP": 143, "KEY_FILE": 144, "KEY_SENDFILE": 145, "KEY_DELETEFILE": 146,
    "KEY_XFER": 147, "KEY_PROG1": 148, "KEY_PROG2": 149, "KEY_WWW": 150, "KEY_MSDOS": 151,
    "KEY_COFFEE": 152, "KEY_ROTATE_DISPLAY": 153, "KEY_CYCLEWINDOWS": 154, "KEY_MAIL": 155,
    "KEY_BOOKMARKS": 156, "KEY_COMPUTER": 157, "KEY_BACK": 158, "KEY_FORWARD": 159,
    "KEY_CLOSECD": 160, "KEY_EJECTCD": 161, "KEY_EJECTCLOSECD": 162, "KEY_NEXTSONG": 163,
    "KEY_PLAYPAUSE": 164, "KEY_PREVIOUSSONG": 165, "KEY_STOPCD": 166, "KEY_RECORD": 167,
    "KEY_REWIND": 168, "KEY_PHONE": 169, "KEY_ISO": 170, "KEY_CONFIG": 171,
    "KEY_HOMEPAGE": 172, "KEY_REFRESH": 173, "KEY_EXIT": 174, "KEY_MOVE": 175, "KEY_EDIT": 176,
    "KEY_SCROLLUP": 177, "KEY_SCROLLDOWN": 178, "KEY_KPLEFTPAREN": 179, "KEY_KPRIGHTPAREN": 180,
    "KEY_NEW": 181, "KEY_REDO": 182,
    "KEY_F13": 183, "KEY_F14": 184, "KEY_F15": 185, "KEY_F16": 186, "KEY_F17": 187,
    "KEY_F18": 188, "KEY_F19": 189, "KEY_F20": 190, "KEY_F21": 191, "KEY_F22": 192,
    "KEY_F23": 193, "KEY_F24": 194,
    "KEY_PLAYCD": 200, "KEY_PAUSECD": 201, "KEY_PROG3": 202, "KEY_PROG4": 203,
    "KEY_ALL_APPLICATIONS": 204, "KEY_SUSPEND": 205, "KEY_CLOSE": 206, "KEY_PLAY": 207,
    "KEY_FASTFORWARD": 208, "KEY_BASSBOOST": 209, "KEY_PRINT": 210, "KEY_HP": 211,
    "KEY_CAMERA": 212, "KEY_SOUND": 213, "KEY_QUESTION": 214, "KEY_EMAIL": 215,
    "KEY_CHAT": 216, "KEY_SEARCH": 217, "KEY_CONNECT": 218, "KEY_FINANCE": 219,
    "KEY_SPORT": 220, "KEY_SHOP": 221, "KEY_ALTERASE": 222, "KEY_CANCEL": 223,
    "KEY_BRIGHTNESSDOWN": 224, "KEY_BRIGHTNESSUP": 225, "KEY_MEDIA": 226,
    "KEY_SWITCHVIDEOMODE": 227, "KEY_KBDILLUMTOGGLE": 228, "KEY_KBDILLUMDOWN": 229,
    "KEY_KBDILLUMUP": 230, "KEY_SEND": 231, "KEY_REPLY": 232, "KEY_FORWARDMAIL": 233,
    "KEY_SAVE": 234, "KEY_DOCUMENTS": 235, "KEY_BATTERY": 236, "KEY_BLUETOOTH": 237,
    "KEY_WLAN": 238, "KEY_UWB": 239, "KEY_UNKNOWN": 240,
    # Mouse buttons (also valid in bindings so a spare mouse can trigger macros)
    "BTN_LEFT": 0x110, "BTN_RIGHT": 0x111, "BTN_MIDDLE": 0x112, "BTN_SIDE": 0x113,
    "BTN_EXTRA": 0x114, "BTN_FORWARD": 0x115, "BTN_BACK": 0x116, "BTN_TASK": 0x117,
}

CODE_NAMES: dict[int, str] = {code: name for name, code in KEY_CODES.items()}

_K = KEY_CODES

EVDEV_TO_HID: dict[int, int] = {
    _K["KEY_A"]: 0x04, _K["KEY_B"]: 0x05, _K["KEY_C"]: 0x06, _K["KEY_D"]: 0x07,
    _K["KEY_E"]: 0x08, _K["KEY_F"]: 0x09, _K["KEY_G"]: 0x0A, _K["KEY_H"]: 0x0B,
    _K["KEY_I"]: 0x0C, _K["KEY_J"]: 0x0D, _K["KEY_K"]: 0x0E, _K["KEY_L"]: 0x0F,
    _K["KEY_M"]: 0x10, _K["KEY_N"]: 0x11, _K["KEY_O"]: 0x12, _K["KEY_P"]: 0x13,
    _K["KEY_Q"]: 0x14, _K["KEY_R"]: 0x15, _K["KEY_S"]: 0x16, _K["KEY_T"]: 0x17,
    _K["KEY_U"]: 0x18, _K["KEY_V"]: 0x19, _K["KEY_W"]: 0x1A, _K["KEY_X"]: 0x1B,
    _K["KEY_Y"]: 0x1C, _K["KEY_Z"]: 0x1D,
    _K["KEY_1"]: 0x1E, _K["KEY_2"]: 0x1F, _K["KEY_3"]: 0x20, _K["KEY_4"]: 0x21,
    _K["KEY_5"]: 0x22, _K["KEY_6"]: 0x23, _K["KEY_7"]: 0x24, _K["KEY_8"]: 0x25,
    _K["KEY_9"]: 0x26, _K["KEY_0"]: 0x27,
    _K["KEY_ENTER"]: 0x28, _K["KEY_ESC"]: 0x29, _K["KEY_BACKSPACE"]: 0x2A,
    _K["KEY_TAB"]: 0x2B, _K["KEY_SPACE"]: 0x2C, _K["KEY_MINUS"]: 0x2D,
    _K["KEY_EQUAL"]: 0x2E, _K["KEY_LEFTBRACE"]: 0x2F, _K["KEY_RIGHTBRACE"]: 0x30,
    _K["KEY_BACKSLASH"]: 0x31, _K["KEY_SEMICOLON"]: 0x33, _K["KEY_APOSTROPHE"]: 0x34,
    _K["KEY_GRAVE"]: 0x35, _K["KEY_COMMA"]: 0x36, _K["KEY_DOT"]: 0x37,
    _K["KEY_SLASH"]: 0x38, _K["KEY_CAPSLOCK"]: 0x39,
    _K["KEY_F1"]: 0x3A, _K["KEY_F2"]: 0x3B, _K["KEY_F3"]: 0x3C, _K["KEY_F4"]: 0x3D,
    _K["KEY_F5"]: 0x3E, _K["KEY_F6"]: 0x3F, _K["KEY_F7"]: 0x40, _K["KEY_F8"]: 0x41,
    _K["KEY_F9"]: 0x42, _K["KEY_F10"]: 0x43, _K["KEY_F11"]: 0x44, _K["KEY_F12"]: 0x45,
    _K["KEY_SYSRQ"]: 0x46, _K["KEY_SCROLLLOCK"]: 0x47, _K["KEY_PAUSE"]: 0x48,
    _K["KEY_INSERT"]: 0x49, _K["KEY_HOME"]: 0x4A, _K["KEY_PAGEUP"]: 0x4B,
    _K["KEY_DELETE"]: 0x4C, _K["KEY_END"]: 0x4D, _K["KEY_PAGEDOWN"]: 0x4E,
    _K["KEY_RIGHT"]: 0x4F, _K["KEY_LEFT"]: 0x50, _K["KEY_DOWN"]: 0x51, _K["KEY_UP"]: 0x52,
    _K["KEY_NUMLOCK"]: 0x53, _K["KEY_KPSLASH"]: 0x54, _K["KEY_KPASTERISK"]: 0x55,
    _K["KEY_KPMINUS"]: 0x56, _K["KEY_KPPLUS"]: 0x57, _K["KEY_KPENTER"]: 0x58,
    _K["KEY_KP1"]: 0x59, _K["KEY_KP2"]: 0x5A, _K["KEY_KP3"]: 0x5B, _K["KEY_KP4"]: 0x5C,
    _K["KEY_KP5"]: 0x5D, _K["KEY_KP6"]: 0x5E, _K["KEY_KP7"]: 0x5F, _K["KEY_KP8"]: 0x60,
    _K["KEY_KP9"]: 0x61, _K["KEY_KP0"]: 0x62, _K["KEY_KPDOT"]: 0x63,
    _K["KEY_102ND"]: 0x64, _K["KEY_COMPOSE"]: 0x65, _K["KEY_MENU"]: 0x65,
    _K["KEY_POWER"]: 0x66, _K["KEY_KPEQUAL"]: 0x67,
    _K["KEY_F13"]: 0x68, _K["KEY_F14"]: 0x69, _K["KEY_F15"]: 0x6A, _K["KEY_F16"]: 0x6B,
    _K["KEY_F17"]: 0x6C, _K["KEY_F18"]: 0x6D, _K["KEY_F19"]: 0x6E, _K["KEY_F20"]: 0x6F,
    _K["KEY_F21"]: 0x70, _K["KEY_F22"]: 0x71, _K["KEY_F23"]: 0x72, _K["KEY_F24"]: 0x73,
    _K["KEY_OPEN"]: 0x74, _K["KEY_HELP"]: 0x75, _K["KEY_PROPS"]: 0x76, _K["KEY_FRONT"]: 0x77,
    _K["KEY_STOP"]: 0x78, _K["KEY_AGAIN"]: 0x79, _K["KEY_UNDO"]: 0x7A, _K["KEY_CUT"]: 0x7B,
    _K["KEY_COPY"]: 0x7C, _K["KEY_PASTE"]: 0x7D, _K["KEY_FIND"]: 0x7E,
    _K["KEY_MUTE"]: 0x7F, _K["KEY_VOLUMEUP"]: 0x80, _K["KEY_VOLUMEDOWN"]: 0x81,
    _K["KEY_KPCOMMA"]: 0x85, _K["KEY_RO"]: 0x87, _K["KEY_KATAKANAHIRAGANA"]: 0x88,
    _K["KEY_YEN"]: 0x89, _K["KEY_HENKAN"]: 0x8A, _K["KEY_MUHENKAN"]: 0x8B,
    _K["KEY_KPJPCOMMA"]: 0x8C, _K["KEY_HANGEUL"]: 0x90, _K["KEY_HANJA"]: 0x91,
    _K["KEY_KATAKANA"]: 0x92, _K["KEY_HIRAGANA"]: 0x93, _K["KEY_ZENKAKUHANKAKU"]: 0x94,
    _K["KEY_KPLEFTPAREN"]: 0xB6, _K["KEY_KPRIGHTPAREN"]: 0xB7,
    _K["KEY_LEFTCTRL"]: 0xE0, _K["KEY_LEFTSHIFT"]: 0xE1, _K["KEY_LEFTALT"]: 0xE2,
    _K["KEY_LEFTMETA"]: 0xE3, _K["KEY_RIGHTCTRL"]: 0xE4, _K["KEY_RIGHTSHIFT"]: 0xE5,
    _K["KEY_RIGHTALT"]: 0xE6, _K["KEY_RIGHTMETA"]: 0xE7,
}

HID_TO_EVDEV: dict[int, int] = {}
for _code, _usage in EVDEV_TO_HID.items():
    # keep the first (canonical) evdev code for each usage
    HID_TO_EVDEV.setdefault(_usage, _code)

MODIFIER_MIN = 0xE0
MODIFIER_MAX = 0xE7

# Boot-protocol descriptor covers array usages 0x00..0x65 only.
BOOT_DESCRIPTOR_MAX_USAGE = 0x65


def is_modifier(usage: int) -> bool:
    return MODIFIER_MIN <= usage <= MODIFIER_MAX


# ----------------------------------------------------------------------------
# Friendly key names for macro definitions
# ----------------------------------------------------------------------------
KEY_ALIASES: dict[str, int] = {
    # modifiers
    "ctrl": 0xE0, "control": 0xE0, "lctrl": 0xE0, "leftctrl": 0xE0,
    "shift": 0xE1, "lshift": 0xE1, "leftshift": 0xE1,
    "alt": 0xE2, "lalt": 0xE2, "leftalt": 0xE2, "option": 0xE2,
    "meta": 0xE3, "win": 0xE3, "windows": 0xE3, "super": 0xE3, "gui": 0xE3,
    "cmd": 0xE3, "lmeta": 0xE3, "lwin": 0xE3,
    "rctrl": 0xE4, "rightctrl": 0xE4,
    "rshift": 0xE5, "rightshift": 0xE5,
    "ralt": 0xE6, "rightalt": 0xE6, "altgr": 0xE6,
    "rmeta": 0xE7, "rwin": 0xE7, "rightmeta": 0xE7,
    # editing / navigation
    "enter": 0x28, "return": 0x28, "esc": 0x29, "escape": 0x29,
    "backspace": 0x2A, "bksp": 0x2A, "tab": 0x2B, "space": 0x2C,
    "minus": 0x2D, "dash": 0x2D, "equal": 0x2E, "equals": 0x2E,
    "leftbrace": 0x2F, "lbracket": 0x2F, "rightbrace": 0x30, "rbracket": 0x30,
    "backslash": 0x31, "semicolon": 0x33, "apostrophe": 0x34, "quote": 0x34,
    "grave": 0x35, "backtick": 0x35, "comma": 0x36, "period": 0x37, "dot": 0x37,
    "slash": 0x38, "capslock": 0x39, "caps": 0x39,
    "printscreen": 0x46, "prtsc": 0x46, "sysrq": 0x46, "scrolllock": 0x47,
    "pause": 0x48, "break": 0x48, "insert": 0x49, "ins": 0x49, "home": 0x4A,
    "pageup": 0x4B, "pgup": 0x4B, "delete": 0x4C, "del": 0x4C, "end": 0x4D,
    "pagedown": 0x4E, "pgdn": 0x4E, "right": 0x4F, "left": 0x50, "down": 0x51, "up": 0x52,
    "numlock": 0x53, "kpslash": 0x54, "kpdivide": 0x54, "kpasterisk": 0x55,
    "kpmultiply": 0x55, "kpminus": 0x56, "kpplus": 0x57, "kpenter": 0x58,
    "kp1": 0x59, "kp2": 0x5A, "kp3": 0x5B, "kp4": 0x5C, "kp5": 0x5D, "kp6": 0x5E,
    "kp7": 0x5F, "kp8": 0x60, "kp9": 0x61, "kp0": 0x62, "kpdot": 0x63, "kpperiod": 0x63,
    "menu": 0x65, "app": 0x65, "application": 0x65, "compose": 0x65,
    "power": 0x66, "kpequal": 0x67, "mute": 0x7F, "volumeup": 0x80, "volumedown": 0x81,
    "plus": 0x2E,  # shifted '=' - handled by macros when typing; bare key is '='
}
for _i in range(1, 25):
    KEY_ALIASES[f"f{_i}"] = 0x3A + (_i - 1) if _i <= 12 else 0x68 + (_i - 13)
for _i, _ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
    KEY_ALIASES[_ch] = 0x04 + _i
for _i, _ch in enumerate("1234567890"):
    KEY_ALIASES[_ch] = 0x1E + _i


def usage_from_name(name: str) -> int:
    """Resolve a key name (alias, KEY_* evdev name or 0xNN usage) to a HID usage."""
    raw = name.strip()
    if not raw:
        raise KeyError("empty key name")
    low = raw.lower()
    if low in KEY_ALIASES:
        return KEY_ALIASES[low]
    upper = raw.upper()
    if upper in KEY_CODES:
        code = KEY_CODES[upper]
        if code in EVDEV_TO_HID:
            return EVDEV_TO_HID[code]
        raise KeyError(f"{raw} has no HID keyboard usage")
    if low.startswith("0x"):
        value = int(low, 16)
        if 0 < value <= 0xFF:
            return value
    raise KeyError(f"unknown key name: {raw}")


# ----------------------------------------------------------------------------
# US QWERTY layout for text typing: char -> (usage, shift)
# ----------------------------------------------------------------------------
US_LAYOUT: dict[str, tuple[int, bool]] = {}
for _i, _ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
    US_LAYOUT[_ch] = (0x04 + _i, False)
    US_LAYOUT[_ch.upper()] = (0x04 + _i, True)
for _i, _ch in enumerate("1234567890"):
    US_LAYOUT[_ch] = (0x1E + _i, False)
for _i, _ch in enumerate("!@#$%^&*()"):
    US_LAYOUT[_ch] = (0x1E + _i, True)
US_LAYOUT.update({
    "\n": (0x28, False), "\r": (0x28, False), "\t": (0x2B, False), " ": (0x2C, False),
    "-": (0x2D, False), "_": (0x2D, True), "=": (0x2E, False), "+": (0x2E, True),
    "[": (0x2F, False), "{": (0x2F, True), "]": (0x30, False), "}": (0x30, True),
    "\\": (0x31, False), "|": (0x31, True), ";": (0x33, False), ":": (0x33, True),
    "'": (0x34, False), '"': (0x34, True), "`": (0x35, False), "~": (0x35, True),
    ",": (0x36, False), "<": (0x36, True), ".": (0x37, False), ">": (0x37, True),
    "/": (0x38, False), "?": (0x38, True),
})
```

## hid_bridge/reports.py

`3471 bytes, 113 lines, sha256 5a35ea23fead9e1db1d2eed1185546de0fa4c5570592ac2098e3a8bc97870c66`

```python
"""HID input report construction."""
from __future__ import annotations

import struct
from typing import Iterable, Iterator

from . import linux_input as li
from .descriptors import ABS_MAX_VALUE
from .keymap import BOOT_DESCRIPTOR_MAX_USAGE, is_modifier

KEYBOARD_IDLE_REPORT = bytes(8)
ERROR_ROLLOVER = 0x01


def keyboard_report(usages: Iterable[int], max_array_usage: int = 0xFF) -> bytes:
    """Build the 8-byte boot keyboard report for the set of pressed usages.

    Usages outside 0x04..max_array_usage are silently dropped (they are not
    representable with the active descriptor).  More than six simultaneous
    non-modifier keys produce the ErrorRollOver phantom state as the HID
    specification requires (all six slots set to 0x01).
    """
    modifiers = 0
    keys: list[int] = []
    for usage in sorted(set(usages)):
        if is_modifier(usage):
            modifiers |= 1 << (usage - 0xE0)
        elif 0x04 <= usage <= max_array_usage:
            keys.append(usage)
    if len(keys) > 6:
        keys = [ERROR_ROLLOVER] * 6
    keys += [0] * (6 - len(keys))
    return bytes([modifiers, 0x00] + keys)


def keyboard_max_array_usage(descriptor_kind: str) -> int:
    return BOOT_DESCRIPTOR_MAX_USAGE if descriptor_kind == "boot" else 0xFF


BUTTON_BITS: dict[int, int] = {
    li.BTN_LEFT: 0,
    li.BTN_RIGHT: 1,
    li.BTN_MIDDLE: 2,
    li.BTN_SIDE: 3,
    li.BTN_BACK: 3,
    li.BTN_EXTRA: 4,
    li.BTN_FORWARD: 4,
}

BUTTON_NAMES: dict[str, int] = {
    "left": 0, "right": 1, "middle": 2, "back": 3, "side": 3, "forward": 4, "extra": 4,
    "1": 0, "2": 1, "3": 2, "4": 3, "5": 4,
}


def clamp(value: int, low: int, high: int) -> int:
    return low if value < low else high if value > high else value


def split_delta(value: int, limit: int = 127) -> Iterator[int]:
    """Yield chunks of ``value`` each within [-limit, limit]."""
    while value > limit:
        yield limit
        value -= limit
    while value < -limit:
        yield -limit
        value += limit
    yield value


def relative_mouse_reports(buttons: int, dx: int, dy: int, wheel: int, button_count: int) -> list[bytes]:
    """Return one or more 4-byte relative mouse reports encoding the motion.

    Motion larger than +-127 is split across several reports so nothing is
    lost, mirroring what a real mouse does at high speed.
    """
    mask = (1 << button_count) - 1
    buttons &= mask
    xs = list(split_delta(dx))
    ys = list(split_delta(dy))
    ws = list(split_delta(wheel))
    count = max(len(xs), len(ys), len(ws))
    xs += [0] * (count - len(xs))
    ys += [0] * (count - len(ys))
    ws += [0] * (count - len(ws))
    return [struct.pack("<Bbbb", buttons, x, y, w) for x, y, w in zip(xs, ys, ws)]


def absolute_mouse_report(buttons: int, x: int, y: int, wheel: int, button_count: int) -> bytes:
    mask = (1 << button_count) - 1
    return struct.pack(
        "<BHHb",
        buttons & mask,
        clamp(x, 0, ABS_MAX_VALUE),
        clamp(y, 0, ABS_MAX_VALUE),
        clamp(wheel, -127, 127),
    )


def scale_abs(value: int, minimum: int, span: int, out_max: int = ABS_MAX_VALUE) -> int:
    """Scale an evdev absolute value from [minimum, minimum+span] to [0, out_max]."""
    if span <= 0:
        return 0
    return clamp(round((value - minimum) * out_max / span), 0, out_max)


LED_BIT_TO_EVDEV: dict[int, int] = {
    0: li.LED_NUML,
    1: li.LED_CAPSL,
    2: li.LED_SCROLLL,
    3: li.LED_COMPOSE,
    4: li.LED_KANA,
}
```

## hid_bridge/linux_input.py

`9954 bytes, 342 lines, sha256 471819847eff6bc8242a9c9cb1453c08d189f289a32015dbcaa72cae683c6bd7`

```python
"""Minimal pure-Python evdev (Linux input subsystem) access.

Only the standard library is used so the bridge has no third-party
dependencies and can be installed on a stock Raspberry Pi OS Lite image
without pip or network access.
"""
from __future__ import annotations

import array
import fcntl
import os
import struct
from dataclasses import dataclass, field
from typing import Iterable

# ----------------------------------------------------------------------------
# Constants from <linux/input-event-codes.h>
# ----------------------------------------------------------------------------
EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03
EV_MSC = 0x04
EV_SW = 0x05
EV_LED = 0x11
EV_REP = 0x14
EV_MAX = 0x1F

SYN_REPORT = 0
SYN_DROPPED = 3

REL_X = 0x00
REL_Y = 0x01
REL_HWHEEL = 0x06
REL_WHEEL = 0x08
REL_WHEEL_HI_RES = 0x0B
REL_HWHEEL_HI_RES = 0x0C
REL_MAX = 0x0F

ABS_X = 0x00
ABS_Y = 0x01
ABS_MAX = 0x3F

LED_NUML = 0x00
LED_CAPSL = 0x01
LED_SCROLLL = 0x02
LED_COMPOSE = 0x03
LED_KANA = 0x04
LED_MAX = 0x0F

KEY_MAX = 0x2FF

BTN_MOUSE = 0x110
BTN_LEFT = 0x110
BTN_RIGHT = 0x111
BTN_MIDDLE = 0x112
BTN_SIDE = 0x113
BTN_EXTRA = 0x114
BTN_FORWARD = 0x115
BTN_BACK = 0x116
BTN_TASK = 0x117
BTN_TOUCH = 0x14A
BTN_TOOL_PEN = 0x140

BUS_USB = 0x03

# ----------------------------------------------------------------------------
# ioctl encoding (asm-generic, valid for arm, arm64 and x86)
# ----------------------------------------------------------------------------
_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = 8
_IOC_SIZESHIFT = 16
_IOC_DIRSHIFT = 30
_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2


def _IOC(direction: int, typ: str, nr: int, size: int) -> int:
    return (
        (direction << _IOC_DIRSHIFT)
        | (ord(typ) << _IOC_TYPESHIFT)
        | (nr << _IOC_NRSHIFT)
        | (size << _IOC_SIZESHIFT)
    )


def _IOR(typ: str, nr: int, size: int) -> int:
    return _IOC(_IOC_READ, typ, nr, size)


def _IOW(typ: str, nr: int, size: int) -> int:
    return _IOC(_IOC_WRITE, typ, nr, size)


EVIOCGVERSION = _IOR("E", 0x01, 4)
EVIOCGID = _IOR("E", 0x02, 8)


def EVIOCGNAME(length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x06, length)


def EVIOCGPHYS(length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x07, length)


def EVIOCGUNIQ(length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x08, length)


def EVIOCGKEY(length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x18, length)


def EVIOCGLED(length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x19, length)


def EVIOCGBIT(ev_type: int, length: int) -> int:
    return _IOC(_IOC_READ, "E", 0x20 + ev_type, length)


def EVIOCGABS(abs_code: int) -> int:
    return _IOR("E", 0x40 + abs_code, 24)


EVIOCGRAB = _IOW("E", 0x90, 4)

# struct input_event { struct timeval time; __u16 type; __u16 code; __s32 value; }
# Native long sizes give 24 bytes on 64-bit and 16 bytes on 32-bit kernels.
INPUT_EVENT = struct.Struct("@llHHi")


@dataclass
class AbsInfo:
    value: int
    minimum: int
    maximum: int
    fuzz: int
    flat: int
    resolution: int

    @property
    def span(self) -> int:
        return max(1, self.maximum - self.minimum)


@dataclass
class DeviceIdentity:
    name: str
    phys: str
    uniq: str
    bustype: int
    vendor: int
    product: int
    version: int


def _bits_from_buffer(buf: bytes) -> set[int]:
    bits: set[int] = set()
    for byte_index, byte in enumerate(buf):
        if not byte:
            continue
        for bit in range(8):
            if byte & (1 << bit):
                bits.add(byte_index * 8 + bit)
    return bits


def list_event_nodes() -> list[str]:
    """Return /dev/input/event* paths sorted numerically."""
    try:
        names = os.listdir("/dev/input")
    except FileNotFoundError:
        return []
    nodes = []
    for name in names:
        if name.startswith("event") and name[5:].isdigit():
            nodes.append((int(name[5:]), f"/dev/input/{name}"))
    return [path for _, path in sorted(nodes)]


class InputDevice:
    """A single /dev/input/eventN device opened non-blocking."""

    def __init__(self, path: str):
        self.path = path
        # O_RDWR so LED state can be written back to the device.
        try:
            self.fd = os.open(path, os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC)
        except PermissionError:
            self.fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
        try:
            self.identity = self._read_identity()
            self.ev_bits = self._read_bits(0, EV_MAX)
            self.key_bits = self._read_bits(EV_KEY, KEY_MAX) if EV_KEY in self.ev_bits else set()
            self.rel_bits = self._read_bits(EV_REL, REL_MAX) if EV_REL in self.ev_bits else set()
            self.abs_bits = self._read_bits(EV_ABS, ABS_MAX) if EV_ABS in self.ev_bits else set()
            self.led_bits = self._read_bits(EV_LED, LED_MAX) if EV_LED in self.ev_bits else set()
            self.absinfo: dict[int, AbsInfo] = {}
            for code in (ABS_X, ABS_Y):
                if code in self.abs_bits:
                    self.absinfo[code] = self._read_absinfo(code)
        except Exception:
            os.close(self.fd)
            raise
        self.grabbed = False
        self._st = os.fstat(self.fd)

    # -- identity -----------------------------------------------------------
    def _read_string(self, request_fn, length: int = 256) -> str:
        buf = bytearray(length)
        try:
            n = fcntl.ioctl(self.fd, request_fn(length), buf)
        except OSError:
            return ""
        if isinstance(n, int) and n > 0:
            raw = bytes(buf[:n])
        else:
            raw = bytes(buf)
        return raw.split(b"\0", 1)[0].decode("utf-8", "replace")

    def _read_identity(self) -> DeviceIdentity:
        buf = bytearray(8)
        fcntl.ioctl(self.fd, EVIOCGID, buf)
        bustype, vendor, product, version = struct.unpack("HHHH", bytes(buf))
        return DeviceIdentity(
            name=self._read_string(EVIOCGNAME),
            phys=self._read_string(EVIOCGPHYS),
            uniq=self._read_string(EVIOCGUNIQ),
            bustype=bustype,
            vendor=vendor,
            product=product,
            version=version,
        )

    def _read_bits(self, ev_type: int, max_code: int) -> set[int]:
        length = max_code // 8 + 1
        buf = bytearray(length)
        fcntl.ioctl(self.fd, EVIOCGBIT(ev_type, length), buf)
        return _bits_from_buffer(bytes(buf))

    def _read_absinfo(self, code: int) -> AbsInfo:
        buf = bytearray(24)
        fcntl.ioctl(self.fd, EVIOCGABS(code), buf)
        return AbsInfo(*struct.unpack("iiiiii", bytes(buf)))

    # -- classification -----------------------------------------------------
    @property
    def name(self) -> str:
        return self.identity.name

    @property
    def is_keyboard(self) -> bool:
        # Any ordinary key (below BTN_MISC 0x100) makes the device usable as
        # a keyboard-like source; this also covers small macro keypads that
        # only expose function keys or digits.
        return any(1 <= code < 0x100 for code in self.key_bits)

    @property
    def is_mouse(self) -> bool:
        has_button = BTN_LEFT in self.key_bits or BTN_TOUCH in self.key_bits
        has_axis = REL_X in self.rel_bits or ABS_X in self.abs_bits
        return has_button and has_axis

    @property
    def has_abs_pointer(self) -> bool:
        return ABS_X in self.abs_bits and ABS_Y in self.abs_bits

    # -- control ------------------------------------------------------------
    def grab(self) -> None:
        if not self.grabbed:
            fcntl.ioctl(self.fd, EVIOCGRAB, 1)
            self.grabbed = True

    def ungrab(self) -> None:
        if self.grabbed:
            try:
                fcntl.ioctl(self.fd, EVIOCGRAB, 0)
            except OSError:
                pass
            self.grabbed = False

    def read_events(self) -> list[tuple[int, int, int]]:
        """Drain pending events. Returns [] if nothing is available.

        Raises OSError (ENODEV) when the device has been unplugged.
        """
        events: list[tuple[int, int, int]] = []
        size = INPUT_EVENT.size
        while True:
            try:
                data = os.read(self.fd, size * 64)
            except BlockingIOError:
                break
            if not data:
                raise OSError(os.strerror(19), 19)  # ENODEV
            for offset in range(0, len(data) - size + 1, size):
                _sec, _usec, ev_type, code, value = INPUT_EVENT.unpack_from(data, offset)
                events.append((ev_type, code, value))
            if len(data) < size * 64:
                break
        return events

    def active_keys(self) -> set[int]:
        """Keys and buttons currently held according to the kernel (EVIOCGKEY).

        Used to resynchronise after the kernel dropped events (SYN_DROPPED).
        """
        length = KEY_MAX // 8 + 1
        buf = bytearray(length)
        try:
            fcntl.ioctl(self.fd, EVIOCGKEY(length), buf)
        except OSError:
            return set()
        return _bits_from_buffer(bytes(buf))

    def set_led(self, led_code: int, on: bool) -> None:
        if led_code not in self.led_bits:
            return
        payload = INPUT_EVENT.pack(0, 0, EV_LED, led_code, 1 if on else 0)
        payload += INPUT_EVENT.pack(0, 0, EV_SYN, SYN_REPORT, 0)
        try:
            os.write(self.fd, payload)
        except OSError:
            pass

    def close(self) -> None:
        if self.fd >= 0:
            self.ungrab()
            try:
                os.close(self.fd)
            finally:
                self.fd = -1

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        ident = self.identity
        return (
            f"InputDevice({self.path!r}, name={ident.name!r}, "
            f"id={ident.vendor:04x}:{ident.product:04x}, kbd={self.is_keyboard}, mouse={self.is_mouse})"
        )
```

## hid_bridge/hidg.py

`11452 bytes, 270 lines, sha256 530e348ca544b314584a5f052d7190ef2a6551c9e357accd7cb4ac1e43c60e4f`

```python
"""Writers for the /dev/hidgN character devices created by usb_f_hid.

Besides sending input reports this module keeps usb_f_hid's GET_REPORT cache
current (kernel >= 6.10, ``GADGET_HID_WRITE_GET_REPORT``).  A real keyboard
answers ``GET_REPORT(Input)`` on the control endpoint with its current state;
without the cache the kernel would wait 2.5 s and then answer with zeros.
"""
from __future__ import annotations

import errno
import fcntl
import logging
import os
import select
import struct
import time

log = logging.getLogger("hid-bridge.hidg")

# Errors that mean "the host is not there right now" rather than a bug.
_DISCONNECT_ERRNOS = {errno.ESHUTDOWN, errno.ENODEV, errno.EPIPE, errno.ECONNRESET}

# <linux/usb/g_hid.h>
#   struct usb_hidg_report { __u8 report_id; __u8 userspace_req; __u16 length;
#                            __u8 data[64]; __u8 padding[4]; };
#   #define GADGET_HID_WRITE_GET_REPORT _IOW('g', 0x42, struct usb_hidg_report)
HIDG_MAX_REPORT_LENGTH = 64
USB_HIDG_REPORT = struct.Struct("=BBH64s4s")
GADGET_HID_WRITE_GET_REPORT = (1 << 30) | (USB_HIDG_REPORT.size << 16) | (ord("g") << 8) | 0x42

BACKOFF_MIN = 0.05
BACKOFF_MAX = 1.0


class HidgDevice:
    def __init__(self, path: str, report_length: int, label: str, idle_report: bytes | None = None):
        if report_length > HIDG_MAX_REPORT_LENGTH:
            raise ValueError("report_length exceeds usb_f_hid's 64-byte GET_REPORT limit")
        self.path = path
        self.report_length = report_length
        self.label = label
        self.idle_report = idle_report if idle_report is not None else bytes(report_length)
        self.fd = -1
        self._rdev = 0
        self.last_report: bytes | None = None
        self.last_sent_at = 0.0
        self.sent = 0
        self.dropped = 0
        self.deferred = 0
        self.disconnected = False
        # usb_f_hid marks the function "disabled" when the host de-configures
        # us; from then on its poll() reports readable forever and read()
        # fails with ENOMEM (SET_REPORT path) or ESHUTDOWN (interrupt OUT
        # path), so the bridge must stop polling the fd for reads until the
        # host configures us again.
        self.host_disabled = False
        # While the host has suspended the bus, dwc2 refuses every queued
        # request (-EAGAIN) although poll() reports the fd writable.  The
        # bridge detects that pattern and retries with a growing delay
        # instead of spinning; ``suspended_path`` (libcomposite's sysfs
        # attribute) lets it wait without even trying while suspended.
        self.suspended_path = ""
        self.backoff_until = 0.0
        self._backoff = 0.0
        self._warned_disconnected = False
        self._warned_backoff = False
        self._get_report_supported = True
        self._cached_get_report: bytes | None = None

    # -- lifecycle -------------------------------------------------------------
    def open(self) -> None:
        if self.fd < 0:
            self.fd = os.open(self.path, os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC)
            self._rdev = os.fstat(self.fd).st_rdev
            self._cached_get_report = None
            self.cache_get_report(self.idle_report)

    def close(self) -> None:
        if self.fd >= 0:
            try:
                os.close(self.fd)
            finally:
                self.fd = -1

    def revalidate(self) -> bool:
        """Reopen if /dev/hidgN was recreated (gadget torn down and rebuilt).

        Returns True when the device node changed.
        """
        if self.fd < 0:
            return False
        try:
            rdev = os.stat(self.path).st_rdev
        except FileNotFoundError:
            rdev = 0
        if rdev == self._rdev:
            return False
        log.warning("%s: %s was recreated; reopening", self.label, self.path)
        self.close()
        self.last_report = None
        self.disconnected = True
        try:
            self.open()
        except OSError as exc:
            log.warning("%s: cannot reopen %s: %s", self.label, self.path, exc.strerror)
        return True

    @property
    def poll_readable(self) -> bool:
        """Whether the bridge should select() this fd for output reports."""
        return self.fd >= 0 and not self.host_disabled

    def host_state_changed(self, udc_state: str) -> None:
        """Re-arm reads once the UDC reports the host configured us again."""
        if self.host_disabled and udc_state == "configured":
            log.info("%s: host configured the interface again", self.label)
            self.host_disabled = False

    def host_suspended(self) -> bool:
        """libcomposite's view of bus suspend (poll-only sysfs attribute)."""
        if not self.suspended_path:
            return False
        try:
            with open(self.suspended_path) as fh:
                return fh.read().strip() == "1"
        except OSError:
            return False

    def enter_backoff(self, now: float) -> None:
        """A write failed although the fd was writable: the bus is suspended."""
        self._backoff = min(max(self._backoff * 2, BACKOFF_MIN), BACKOFF_MAX)
        self.backoff_until = now + self._backoff
        if not self._warned_backoff:
            log.info("%s: host is not accepting reports (bus suspended?); retrying with backoff", self.label)
            self._warned_backoff = True

    def extend_backoff(self, now: float, seconds: float = 0.25) -> None:
        self.backoff_until = now + seconds

    def _clear_backoff(self) -> None:
        if self._warned_backoff:
            log.info("%s: host accepting reports again", self.label)
        self._backoff = 0.0
        self.backoff_until = 0.0
        self._warned_backoff = False

    # -- GET_REPORT cache -------------------------------------------------------
    def cache_get_report(self, report: bytes) -> None:
        """Publish ``report`` as the answer to GET_REPORT(Input) on EP0."""
        if not self._get_report_supported or self.fd < 0 or report == self._cached_get_report:
            return
        payload = USB_HIDG_REPORT.pack(0, 0, len(report), report.ljust(HIDG_MAX_REPORT_LENGTH, b"\0"), b"\0" * 4)
        try:
            fcntl.ioctl(self.fd, GADGET_HID_WRITE_GET_REPORT, payload)
        except OSError as exc:
            if exc.errno in (errno.ENOTTY, errno.EINVAL):
                self._get_report_supported = False
                log.info("%s: kernel lacks the f_hid GET_REPORT cache ioctl; the kernel answers GET_REPORT itself", self.label)
            else:
                log.warning("%s: GET_REPORT cache update failed: %s", self.label, exc.strerror)
            return
        self._cached_get_report = report

    # -- input reports ----------------------------------------------------------
    def write_report(self, report: bytes, force: bool = False, get_report: bytes | None = None) -> bool:
        """Try to send ``report`` once, without blocking.

        Returns True when the report was handed to the kernel (or was
        identical to the last one and ``force`` is not set).  Returns False
        when it could not go out right now: either the previous report is
        still waiting for the host to poll (``usb_f_hid`` keeps exactly one
        IN request in flight; the fd becomes writable once it completes),
        the bus is suspended, or the host is not connected.  The caller
        keeps its own "latest state" and retries when the fd is writable,
        which is how a real keyboard or mouse behaves: one report register,
        latest state wins, motion accumulates between polls.

        ``get_report`` overrides what GET_REPORT should answer from now on;
        it defaults to ``report`` (correct for state-based reports).
        """
        if len(report) != self.report_length:
            raise ValueError(f"{self.label}: report must be {self.report_length} bytes, got {len(report)}")
        if self.fd < 0:
            try:
                self.open()
            except OSError as exc:
                self._note_disconnect(exc)
                self.dropped += 1
                return False
        self.cache_get_report(report if get_report is None else get_report)
        if not force and report == self.last_report:
            return True
        try:
            os.write(self.fd, report)
        except BlockingIOError:
            # Previous report not yet collected by the host, or bus suspended.
            self.deferred += 1
            return False
        except OSError as exc:
            self.dropped += 1
            if exc.errno in _DISCONNECT_ERRNOS:
                self._note_disconnect(exc)
                return False
            raise
        self.last_report = report
        self.last_sent_at = time.monotonic()
        self.sent += 1
        if self.backoff_until or self._backoff:
            self._clear_backoff()
        if self.disconnected or self.host_disabled:
            log.info("%s: host connected again", self.label)
            self.disconnected = False
            self.host_disabled = False
            self._warned_disconnected = False
        return True

    def write_report_blocking(self, report: bytes, timeout: float) -> bool:
        """Best-effort delivery with a bounded wait; used only at shutdown."""
        deadline = time.monotonic() + timeout
        while True:
            if self.write_report(report, force=True):
                return True
            if self.disconnected or self.host_disabled or self.fd < 0:
                return False
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            try:
                select.select([], [self.fd], [], min(remaining, 0.02))
            except OSError:
                return False

    def _note_disconnect(self, exc: OSError) -> None:
        self.disconnected = True
        self.last_report = None
        if not self._warned_disconnected:
            log.warning("%s: host not connected (%s); reports are dropped until it enumerates us", self.label, exc.strerror)
            self._warned_disconnected = True

    # -- output reports (LEDs) ---------------------------------------------------
    def read_output_report(self) -> bytes | None:
        """Read a pending output report (keyboard LED byte). None if nothing is pending."""
        if self.fd < 0:
            return None
        try:
            data = os.read(self.fd, HIDG_MAX_REPORT_LENGTH)
        except BlockingIOError:
            return None
        except OSError as exc:
            if exc.errno == errno.ENOMEM or exc.errno in _DISCONNECT_ERRNOS:
                # usb_f_hid's "function disabled" signal: the host went away.
                if not self.host_disabled:
                    log.info("%s: host de-configured the interface; waiting for it to come back", self.label)
                self.host_disabled = True
                self.disconnected = True
                self.last_report = None
                return None
            raise
        return data or None

    def stats(self) -> dict:
        return {
            "device": self.path,
            "sent": self.sent,
            "deferred": self.deferred,
            "dropped": self.dropped,
            "host_connected": not (self.disconnected or self.host_disabled),
            "backing_off": self.backoff_until > 0,
            "get_report_cache": self._get_report_supported,
        }
```

## hid_bridge/gadget.py

`18729 bytes, 443 lines, sha256 db9841d434990a24a6538d3cf66daf23641e7ace0e7faf356d523650272725ba`

```python
"""configfs/libcomposite USB gadget management.

Creates a single-configuration gadget with two HID functions:

* interface 0: boot-protocol keyboard  -> /dev/hidgN (keyboard)
* interface 1: boot-protocol mouse     -> /dev/hidgM (mouse)

Everything the kernel lets user space control is pinned to the values a
plain full-speed keyboard/mouse combo exposes.  See docs/usb-identity.md for
the fields libcomposite fixes itself.
"""
from __future__ import annotations

import errno
import json
import logging
import os
import re
import stat
import subprocess
import time

from .config import Config
from .descriptors import (
    HID_PROTOCOL_KEYBOARD,
    HID_PROTOCOL_MOUSE,
    HID_SUBCLASS_BOOT,
    KEYBOARD_REPORT_LENGTH,
    keyboard_report_descriptor,
    mouse_report_descriptor,
    mouse_report_length,
)

log = logging.getLogger("hid-bridge.gadget")

STATE_DIR = "/run/hid-bridge"
STATE_FILE = os.path.join(STATE_DIR, "gadget.json")
UDC_SYSFS = "/sys/class/udc"

KEYBOARD_FUNCTION = "hid.kbd"
MOUSE_FUNCTION = "hid.mouse"


class GadgetError(Exception):
    pass


def _write(path: str, value: str | bytes) -> None:
    mode = "wb" if isinstance(value, bytes) else "w"
    with open(path, mode) as fh:
        fh.write(value)


def _read(path: str, default: str = "") -> str:
    try:
        with open(path) as fh:
            return fh.read().strip()
    except OSError:
        return default


def _write_optional(path: str, value: str, feature: str, warnings: list[str]) -> bool:
    if not os.path.exists(path):
        warnings.append(f"kernel lacks {feature} ({os.path.basename(path)}); skipped")
        return False
    try:
        _write(path, value)
        return True
    except OSError as exc:
        warnings.append(f"could not set {feature}: {exc.strerror}")
        return False


def list_udcs() -> list[str]:
    try:
        return sorted(os.listdir(UDC_SYSFS))
    except FileNotFoundError:
        return []


def udc_lpm_enabled(udc: str) -> bool | None:
    """Whether dwc2 runs with LPM enabled (decides bcdUSB 2.00 vs 2.01 + BOS).

    Read from debugfs; None when debugfs is unavailable.
    """
    text = _read(f"/sys/kernel/debug/usb/{udc}/params")
    match = re.search(r"^\s*lpm\s*[:=]\s*(\d)", text, re.M)
    return None if not match else match.group(1) == "1"


def udc_current_state(udc: str) -> str:
    """Cheap read of /sys/class/udc/<udc>/state for the bridge's periodic poll."""
    return _read(os.path.join(UDC_SYSFS, udc, "state"), "unknown")


def udc_state(udc: str, full_speed_patched: bool = False) -> dict:
    """UDC state; ``full_speed_patched`` = kernel-patches/0002 present and max_speed full-speed."""
    base = os.path.join(UDC_SYSFS, udc)
    lpm = udc_lpm_enabled(udc)
    if full_speed_patched:
        wire = "0x0200 (kernel-patches/0002: no LPM/BOS at full speed)"
    elif lpm is None:
        wire = "unknown"
    else:
        wire = "0x0201 (+BOS)" if lpm else "0x0200"
    return {
        "udc": udc,
        "state": _read(os.path.join(base, "state"), "unknown"),
        "current_speed": _read(os.path.join(base, "current_speed"), "unknown"),
        "maximum_speed": _read(os.path.join(base, "maximum_speed"), "unknown"),
        "function": _read(os.path.join(base, "function"), ""),
        "lpm": lpm,
        "bcdUSB_on_wire": wire,
        "suspended": _read(os.path.join(base, "gadget", "suspended"), "n/a"),
    }


def _find_hidg_by_dev(major_minor: str) -> str | None:
    try:
        major_s, minor_s = major_minor.strip().split(":")
        wanted = os.makedev(int(major_s), int(minor_s))
    except ValueError:
        return None
    try:
        names = os.listdir("/dev")
    except OSError:
        return None
    for name in names:
        if not name.startswith("hidg"):
            continue
        path = f"/dev/{name}"
        try:
            st = os.stat(path)
        except OSError:
            continue
        if stat.S_ISCHR(st.st_mode) and st.st_rdev == wanted:
            return path
    return None


class Gadget:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.g = cfg.gadget
        self.path = os.path.join(self.g.configfs, self.g.name)
        self.warnings: list[str] = []

    # -- helpers ---------------------------------------------------------------
    def _p(self, *parts: str) -> str:
        return os.path.join(self.path, *parts)

    def exists(self) -> bool:
        return os.path.isdir(self.path)

    def bound_udc(self) -> str:
        return _read(self._p("UDC")) if self.exists() else ""

    def ensure_configfs(self) -> None:
        if os.path.isdir(self.g.configfs):
            return
        if not os.path.isdir("/sys/kernel/config"):
            subprocess.run(["mount", "-t", "configfs", "none", "/sys/kernel/config"], check=False)
        if not os.path.isdir(self.g.configfs):
            subprocess.run(["modprobe", "libcomposite"], check=False)
        for _ in range(20):
            if os.path.isdir(self.g.configfs):
                return
            time.sleep(0.1)
        raise GadgetError(f"{self.g.configfs} is not available: is libcomposite loaded and configfs mounted?")

    def pick_udc(self, timeout: float = 15.0) -> str:
        deadline = time.monotonic() + timeout
        while True:
            udcs = list_udcs()
            if self.g.udc:
                if self.g.udc in udcs:
                    return self.g.udc
            elif udcs:
                if len(udcs) > 1:
                    self.warnings.append(f"several UDCs present ({', '.join(udcs)}); using {udcs[0]}")
                return udcs[0]
            if time.monotonic() >= deadline:
                break
            time.sleep(0.25)
        wanted = self.g.udc or "any"
        raise GadgetError(
            f"no USB device controller found (wanted: {wanted}). "
            "Add 'dtoverlay=dwc2,dr_mode=peripheral' to /boot/firmware/config.txt, "
            "load the dwc2 module and reboot."
        )

    # -- descriptors -----------------------------------------------------------
    def keyboard_descriptor(self) -> bytes:
        return keyboard_report_descriptor(self.cfg.keyboard.descriptor == "extended")

    def mouse_descriptor(self) -> bytes:
        return mouse_report_descriptor(self.cfg.mouse.mode, self.cfg.mouse.buttons)

    # -- lifecycle -------------------------------------------------------------
    def up(self) -> dict:
        self.warnings = []
        self.ensure_configfs()
        if self.exists():
            if self.bound_udc():
                log.info("gadget %s already bound to %s", self.g.name, self.bound_udc())
                devices = self.resolve_devices()
                self._write_state(devices)
                return devices
            log.info("gadget %s exists but is unbound; rebuilding", self.g.name)
            self.down()

        g = self.g
        os.makedirs(self._p("strings", "0x409"), exist_ok=True)
        os.makedirs(self._p("configs", "c.1"), exist_ok=True)
        os.makedirs(self._p("functions", KEYBOARD_FUNCTION), exist_ok=True)
        os.makedirs(self._p("functions", MOUSE_FUNCTION), exist_ok=True)

        # Device descriptor
        _write(self._p("idVendor"), f"0x{g.vendor_id:04x}")
        _write(self._p("idProduct"), f"0x{g.product_id:04x}")
        _write(self._p("bcdDevice"), f"0x{g.device_version:04x}")
        # libcomposite recomputes bcdUSB (0x0200, or 0x0201 with LPM) and
        # bMaxPacketSize0 (dwc2 EP0 = 64) when answering GET_DESCRIPTOR; write
        # the values it will emit so configfs reflects the wire.
        _write(self._p("bcdUSB"), "0x0200")
        _write(self._p("bDeviceClass"), "0x00")     # class defined per interface
        _write(self._p("bDeviceSubClass"), "0x00")
        _write(self._p("bDeviceProtocol"), "0x00")
        _write(self._p("bMaxPacketSize0"), "0x40")
        _write_optional(self._p("max_speed"), g.max_speed, "max_speed selection", self.warnings)

        # Strings.  Once the language directory exists libcomposite always
        # allocates iManufacturer=1, iProduct=2, iSerialNumber=3 and answers an
        # unset one with an empty string descriptor.  A real keyboard has
        # either a set of real strings or none at all, so either fill all
        # three or leave all three empty (no strings directory).
        if g.manufacturer or g.product or g.serial:
            for attr, value in (("manufacturer", g.manufacturer), ("product", g.product), ("serialnumber", g.serial)):
                if value:
                    _write(self._p("strings", "0x409", attr), value)
                else:
                    self.warnings.append(
                        f"gadget.{attr} is empty: the kernel presents string #{('manufacturer', 'product', 'serialnumber').index(attr) + 1} "
                        "as an empty descriptor; set it or clear all three strings")
        else:
            os.rmdir(self._p("strings", "0x409"))

        # Configuration descriptor: bus powered (bit 7 always set), optional
        # self-powered (bit 6) and remote-wakeup (bit 5) bits.
        attrs = 0x80 | (0x40 if g.self_powered else 0) | (0x20 if g.remote_wakeup else 0)
        _write(self._p("configs", "c.1", "bmAttributes"), f"0x{attrs:02x}")
        _write(self._p("configs", "c.1", "MaxPower"), str(g.max_power_ma))

        # Keyboard function
        kbd = self._p("functions", KEYBOARD_FUNCTION)
        _write(os.path.join(kbd, "protocol"), str(HID_PROTOCOL_KEYBOARD))
        _write(os.path.join(kbd, "subclass"), str(HID_SUBCLASS_BOOT))
        _write(os.path.join(kbd, "report_length"), str(KEYBOARD_REPORT_LENGTH))
        _write(os.path.join(kbd, "report_desc"), self.keyboard_descriptor())
        _write_optional(os.path.join(kbd, "no_out_endpoint"), "1", "single-IN-endpoint HID (no_out_endpoint)", self.warnings)
        _write_optional(os.path.join(kbd, "strict_report_types"), "1", "report-type checking of GET/SET_REPORT (strict_report_types, see kernel-patches/)", self.warnings)
        if g.remote_wakeup:
            _write_optional(os.path.join(kbd, "wakeup_on_write"), "1", "remote wakeup on keypress (wakeup_on_write)", self.warnings)
        _write_optional(os.path.join(kbd, "interval"), str(self.cfg.keyboard.poll_interval_ms), "keyboard bInterval", self.warnings)

        # Mouse function
        mouse = self._p("functions", MOUSE_FUNCTION)
        if self.cfg.mouse.mode == "relative":
            _write(os.path.join(mouse, "protocol"), str(HID_PROTOCOL_MOUSE))
            _write(os.path.join(mouse, "subclass"), str(HID_SUBCLASS_BOOT))
        else:
            # An absolute pointer is not a boot-protocol mouse; say so honestly.
            _write(os.path.join(mouse, "protocol"), "0")
            _write(os.path.join(mouse, "subclass"), "0")
        _write(os.path.join(mouse, "report_length"), str(mouse_report_length(self.cfg.mouse.mode)))
        _write(os.path.join(mouse, "report_desc"), self.mouse_descriptor())
        _write_optional(os.path.join(mouse, "no_out_endpoint"), "1", "single-IN-endpoint HID (no_out_endpoint)", self.warnings)
        _write_optional(os.path.join(mouse, "strict_report_types"), "1", "report-type checking of GET/SET_REPORT (strict_report_types, see kernel-patches/)", self.warnings)
        if g.remote_wakeup:
            _write_optional(os.path.join(mouse, "wakeup_on_write"), "1", "remote wakeup on mouse activity (wakeup_on_write)", self.warnings)
        _write_optional(os.path.join(mouse, "interval"), str(self.cfg.mouse.poll_interval_ms), "mouse bInterval", self.warnings)

        # Interface order = link order: keyboard first, mouse second.
        os.symlink(kbd, self._p("configs", "c.1", KEYBOARD_FUNCTION))
        os.symlink(mouse, self._p("configs", "c.1", MOUSE_FUNCTION))

        udc = self.pick_udc()
        try:
            _write(self._p("UDC"), udc)
        except OSError as exc:
            if exc.errno == errno.EBUSY:
                raise GadgetError(f"UDC {udc} is busy: another gadget is bound to it (check {self.g.configfs})") from exc
            raise
        log.info("gadget %s bound to %s", g.name, udc)

        devices = self.resolve_devices()
        self._prime_get_report(devices)
        self._write_state(devices)
        for warning in self.warnings:
            log.warning("%s", warning)
        return devices

    def _prime_get_report(self, devices: dict) -> None:
        """Answer GET_REPORT immediately even before hid-bridge runs.

        Without a cached report usb_f_hid waits 2.5 s and answers zeros; a
        real keyboard answers at once.
        """
        from .hidg import HidgDevice
        for role, length in (("keyboard", devices["keyboard_report_length"]), ("mouse", devices["mouse_report_length"])):
            try:
                sink = HidgDevice(devices[role], length, role)
                sink.open()
                sink.close()
            except OSError as exc:
                self.warnings.append(f"could not prime GET_REPORT for {role}: {exc.strerror}")

    def down(self) -> None:
        if not self.exists():
            return
        try:
            if self.bound_udc():
                _write(self._p("UDC"), "")
        except OSError as exc:
            log.warning("unbinding UDC failed: %s", exc)
        for func in (KEYBOARD_FUNCTION, MOUSE_FUNCTION):
            link = self._p("configs", "c.1", func)
            if os.path.islink(link):
                os.unlink(link)
        for directory in (
            self._p("configs", "c.1", "strings", "0x409"),
            self._p("configs", "c.1"),
            self._p("functions", KEYBOARD_FUNCTION),
            self._p("functions", MOUSE_FUNCTION),
            self._p("strings", "0x409"),
            self.path,
        ):
            if os.path.isdir(directory):
                try:
                    os.rmdir(directory)
                except OSError as exc:
                    log.warning("rmdir %s: %s", directory, exc.strerror)
        try:
            os.unlink(STATE_FILE)
        except OSError:
            pass
        log.info("gadget %s removed", self.g.name)

    # -- device resolution ------------------------------------------------------
    def resolve_devices(self, timeout: float = 5.0) -> dict:
        """Map the two functions to their /dev/hidgN nodes."""
        result: dict[str, str] = {}
        deadline = time.monotonic() + timeout
        while True:
            for role, func in (("keyboard", KEYBOARD_FUNCTION), ("mouse", MOUSE_FUNCTION)):
                if role in result:
                    continue
                dev_attr = _read(self._p("functions", func, "dev"))
                path = _find_hidg_by_dev(dev_attr) if dev_attr else None
                if path:
                    result[role] = path
            if len(result) == 2 or time.monotonic() >= deadline:
                break
            time.sleep(0.1)
        if len(result) < 2:
            # Old kernels without the 'dev' attribute: fall back to creation order.
            fallback = {"keyboard": "/dev/hidg0", "mouse": "/dev/hidg1"}
            for role, path in fallback.items():
                if role not in result and os.path.exists(path):
                    result[role] = path
                    self.warnings.append(f"assumed {path} is the {role} (kernel has no hid 'dev' attribute)")
        if len(result) < 2:
            raise GadgetError("could not find /dev/hidg* devices for the gadget functions")
        return {
            "gadget": self.path,
            "udc": self.bound_udc(),
            "keyboard": result["keyboard"],
            "mouse": result["mouse"],
            "keyboard_report_length": KEYBOARD_REPORT_LENGTH,
            "mouse_report_length": mouse_report_length(self.cfg.mouse.mode),
        }

    def _write_state(self, devices: dict) -> None:
        try:
            os.makedirs(STATE_DIR, exist_ok=True)
            with open(STATE_FILE, "w") as fh:
                json.dump(devices, fh, indent=2)
        except OSError as exc:
            log.warning("cannot write %s: %s", STATE_FILE, exc)

    def patched_kernel(self) -> bool:
        """True when the kernel carries kernel-patches/ (detected via the 0003 attribute)."""
        return os.path.exists(self._p("functions", KEYBOARD_FUNCTION, "strict_report_types"))

    def status(self) -> dict:
        info: dict = {"gadget": self.path, "exists": self.exists(), "bound": False}
        if not self.exists():
            info["udcs"] = list_udcs()
            return info
        udc = self.bound_udc()
        info["bound"] = bool(udc)
        info["descriptor"] = {
            "idVendor": _read(self._p("idVendor")),
            "idProduct": _read(self._p("idProduct")),
            "bcdDevice": _read(self._p("bcdDevice")),
            "bcdUSB": _read(self._p("bcdUSB")),
            "max_speed": _read(self._p("max_speed"), "n/a"),
            "manufacturer": _read(self._p("strings", "0x409", "manufacturer")),
            "product": _read(self._p("strings", "0x409", "product")),
            "serialnumber": _read(self._p("strings", "0x409", "serialnumber")),
            "bmAttributes": _read(self._p("configs", "c.1", "bmAttributes")),
            "MaxPower": _read(self._p("configs", "c.1", "MaxPower")),
        }
        info["functions"] = {}
        for role, func in (("keyboard", KEYBOARD_FUNCTION), ("mouse", MOUSE_FUNCTION)):
            base = self._p("functions", func)
            if os.path.isdir(base):
                info["functions"][role] = {
                    "protocol": _read(os.path.join(base, "protocol")),
                    "subclass": _read(os.path.join(base, "subclass")),
                    "report_length": _read(os.path.join(base, "report_length")),
                    "no_out_endpoint": _read(os.path.join(base, "no_out_endpoint"), "n/a"),
                    "strict_report_types": _read(os.path.join(base, "strict_report_types"), "n/a"),
                    "wakeup_on_write": _read(os.path.join(base, "wakeup_on_write"), "n/a"),
                    "interval": _read(os.path.join(base, "interval"), "n/a"),
                    "dev": _read(os.path.join(base, "dev"), "n/a"),
                }
        info["patched_kernel"] = self.patched_kernel()
        if udc:
            info["udc"] = udc_state(udc, self.patched_kernel() and self.g.max_speed == "full-speed")
            try:
                info["devices"] = self.resolve_devices(timeout=0.5)
            except GadgetError as exc:
                info["devices_error"] = str(exc)
        return info


def load_state() -> dict | None:
    try:
        with open(STATE_FILE) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None
```

## hid_bridge/macros.py

`13958 bytes, 385 lines, sha256 8a35974bfa54804639de0aa19cb43b92ff04879e4c09edc407b2451851252bb4`

```python
"""Macro definitions and the cooperative macro engine.

A macro is a list of step strings.  Each step is one of::

    <combo>                 tap the key combination, e.g. "ctrl+alt+delete"
    tap <combo>             same as a bare combo
    press <combo>           press and hold
    release <combo>         release specific keys
    release all             release every key and mouse button held by macros
    type <text>             type text using the US layout (rest of the line)
    wait <ms>               pause
    mouse move <dx> <dy>    relative motion
    mouse to <x> <y>        absolute position 0..32767 (absolute mouse mode)
    mouse click <button> [n]  click n times (left/right/middle/back/forward)
    mouse down <button>
    mouse up <button>
    mouse wheel <n>         positive = away from the user
    macro <name>            run another macro inline (max depth 8)

Steps execute cooperatively from the bridge's main loop: each step yields a
delay and pass-through input keeps flowing while a macro is waiting.
"""
from __future__ import annotations

import heapq
import itertools
import logging
import random
import shlex
import time
from dataclasses import dataclass, field
from typing import Callable, Generator, Iterable, Protocol

from .keymap import US_LAYOUT, is_modifier, usage_from_name
from .reports import BUTTON_NAMES

log = logging.getLogger("hid-bridge.macros")

MAX_DEPTH = 8


class MacroError(Exception):
    pass


@dataclass
class Step:
    kind: str
    keys: tuple[int, ...] = ()
    text: str = ""
    ms: int = 0
    dx: int = 0
    dy: int = 0
    button: int = 0
    count: int = 1
    name: str = ""

    def describe(self) -> str:
        if self.kind == "type":
            return f"type {self.text!r}"
        if self.kind in ("tap", "press", "release"):
            return f"{self.kind} {'+'.join(f'0x{u:02x}' for u in self.keys)}"
        if self.kind == "wait":
            return f"wait {self.ms}"
        if self.kind == "macro":
            return f"macro {self.name}"
        return self.kind


def parse_combo(text: str) -> tuple[int, ...]:
    parts = [p for p in text.strip().split("+") if p != ""]
    if text.strip().endswith("+") and text.strip() != "+":
        # "ctrl++" means ctrl plus the '+' key
        parts.append("plus")
    if text.strip() == "+":
        parts = ["plus"]
    if not parts:
        raise MacroError("empty key combination")
    usages: list[int] = []
    for part in parts:
        try:
            usage = usage_from_name(part)
        except KeyError as exc:
            raise MacroError(str(exc)) from exc
        if usage not in usages:
            usages.append(usage)
    return tuple(usages)


def _int_arg(value: str, what: str) -> int:
    try:
        return int(value, 0)
    except ValueError:
        raise MacroError(f"{what}: expected an integer, got {value!r}")


def _button(value: str) -> int:
    key = value.lower()
    if key not in BUTTON_NAMES:
        raise MacroError(f"unknown mouse button {value!r} (use left/right/middle/back/forward)")
    return BUTTON_NAMES[key]


def parse_step(text: str, known_macros: dict[str, Iterable[str]] | None = None) -> Step:
    raw = text.strip()
    if not raw:
        raise MacroError("empty step")
    head, _, rest = raw.partition(" ")
    verb = head.lower()
    rest = rest.strip()

    if verb == "type":
        body = raw[len(head):]
        if body.startswith(" "):
            body = body[1:]
        return Step("type", text=body)
    if verb == "wait":
        ms = _int_arg(rest, "wait")
        if ms < 0:
            raise MacroError("wait: delay must be >= 0")
        return Step("wait", ms=ms)
    if verb in ("tap", "press"):
        if not rest:
            raise MacroError(f"{verb}: missing key combination")
        return Step(verb, keys=parse_combo(rest))
    if verb == "release":
        if rest.lower() == "all":
            return Step("release_all")
        if not rest:
            raise MacroError("release: missing key combination (or 'all')")
        return Step("release", keys=parse_combo(rest))
    if verb == "macro":
        if not rest:
            raise MacroError("macro: missing name")
        if known_macros is not None and rest not in known_macros:
            raise MacroError(f"macro: no such macro {rest!r}")
        return Step("macro", name=rest)
    if verb == "mouse":
        args = shlex.split(rest)
        if not args:
            raise MacroError("mouse: missing sub-command")
        sub = args[0].lower()
        if sub == "move" and len(args) == 3:
            return Step("mouse_move", dx=_int_arg(args[1], "dx"), dy=_int_arg(args[2], "dy"))
        if sub == "to" and len(args) == 3:
            return Step("mouse_to", dx=_int_arg(args[1], "x"), dy=_int_arg(args[2], "y"))
        if sub == "click" and len(args) in (2, 3):
            count = _int_arg(args[2], "count") if len(args) == 3 else 1
            if count < 1:
                raise MacroError("mouse click: count must be >= 1")
            return Step("mouse_click", button=_button(args[1]), count=count)
        if sub == "down" and len(args) == 2:
            return Step("mouse_down", button=_button(args[1]))
        if sub == "up" and len(args) == 2:
            return Step("mouse_up", button=_button(args[1]))
        if sub == "wheel" and len(args) == 2:
            return Step("mouse_wheel", dy=_int_arg(args[1], "wheel"))
        raise MacroError(f"mouse: bad sub-command {rest!r}")
    # Anything else is a bare key combination.
    return Step("tap", keys=parse_combo(raw))


class MacroTarget(Protocol):
    """What the macro engine needs from the bridge."""

    def macro_keys_changed(self) -> None: ...
    def macro_mouse_move(self, dx: int, dy: int, wheel: int) -> None: ...
    def macro_mouse_to(self, x: int, y: int) -> None: ...
    def macro_buttons_changed(self) -> None: ...


@dataclass(order=True)
class _Scheduled:
    when: float
    seq: int
    task: "MacroTask" = field(compare=False)


class MacroTask:
    def __init__(self, engine: "MacroEngine", label: str, steps: list[Step], depth: int = 0):
        self.engine = engine
        self.label = label
        self.steps = steps
        self.depth = depth
        self.gen = self._run()
        self.done = False

    def _run(self) -> Generator[float, None, None]:
        eng = self.engine
        for step in self.steps:
            tap = eng.tap_delay()
            gap = eng.gap_delay()
            kind = step.kind
            if kind == "tap":
                yield from self._tap(step.keys)
                yield gap
            elif kind == "press":
                eng.press(step.keys)
                yield gap
            elif kind == "release":
                eng.release(step.keys)
                yield gap
            elif kind == "release_all":
                eng.release_all()
                yield gap
            elif kind == "type":
                for ch in step.text:
                    entry = US_LAYOUT.get(ch)
                    if entry is None:
                        log.warning("macro %s: cannot type %r with the US layout, skipped", self.label, ch)
                        continue
                    usage, shift = entry
                    keys = (0xE1, usage) if shift else (usage,)
                    yield from self._tap(keys)
                    yield eng.gap_delay()
            elif kind == "wait":
                yield step.ms / 1000.0
            elif kind == "mouse_move":
                eng.target.macro_mouse_move(step.dx, step.dy, 0)
                yield gap
            elif kind == "mouse_to":
                eng.target.macro_mouse_to(step.dx, step.dy)
                yield gap
            elif kind == "mouse_wheel":
                eng.target.macro_mouse_move(0, 0, step.dy)
                yield gap
            elif kind == "mouse_down":
                eng.button(step.button, True)
                yield gap
            elif kind == "mouse_up":
                eng.button(step.button, False)
                yield gap
            elif kind == "mouse_click":
                for _ in range(step.count):
                    eng.button(step.button, True)
                    yield eng.tap_delay()
                    eng.button(step.button, False)
                    yield eng.gap_delay()
            elif kind == "macro":
                if self.depth >= MAX_DEPTH:
                    raise MacroError(f"macro nesting deeper than {MAX_DEPTH} ({step.name})")
                sub_steps = eng.compile(step.name)
                sub = MacroTask(eng, f"{self.label}>{step.name}", sub_steps, self.depth + 1)
                yield from sub.gen
            else:  # pragma: no cover
                raise MacroError(f"unknown step kind {kind}")


    def _tap(self, keys: tuple[int, ...]) -> Generator[float, None, None]:
        """Press and release ``keys`` the way fingers do.

        Modifiers go down in their own report a little before the key and
        come up a little after it; a human never lands Shift and the letter
        in the same 10 ms poll, and keystroke analysis knows that.
        """
        eng = self.engine
        mods = tuple(k for k in keys if is_modifier(k))
        plain = tuple(k for k in keys if not is_modifier(k))
        if mods and plain:
            eng.press(mods)
            yield eng.lead_delay()
            eng.press(plain)
            yield eng.tap_delay()
            eng.release(plain)
            yield eng.lead_delay()
            eng.release(mods)
        else:
            eng.press(keys)
            yield eng.tap_delay()
            eng.release(keys)


class MacroEngine:
    def __init__(self, target: MacroTarget, macros: dict[str, list[str]], tap_ms: int = 30, step_ms: int = 20,
                 jitter_ms: int = 0):
        self.target = target
        self.macros = macros
        self.tap_ms = tap_ms
        self.step_ms = step_ms
        self.jitter_ms = jitter_ms
        self._random = random.Random()
        self.pressed: set[int] = set()
        self.buttons = 0
        self._queue: list[_Scheduled] = []
        self._seq = itertools.count()
        self._compiled: dict[str, list[Step]] = {}
        self.running = 0
        self.completed = 0
        self.failed = 0

    def _jitter(self) -> float:
        # Right-skewed (mode near 30 % of the range) rather than flat: human
        # hold and gap times cluster near a minimum with a long tail.
        if not self.jitter_ms:
            return 0.0
        return self._random.triangular(0, self.jitter_ms, self.jitter_ms * 0.3) / 1000.0

    def tap_delay(self) -> float:
        """Hold time for a tap; randomised by ``jitter_ms`` so scripted input
        does not have the metronomic cadence a keystroke-timing analysis
        would flag."""
        return self.tap_ms / 1000.0 + self._jitter()

    def gap_delay(self) -> float:
        return self.step_ms / 1000.0 + self._jitter()

    def lead_delay(self) -> float:
        """Modifier lead/lag around a key: half a tap plus jitter."""
        return self.tap_ms / 2000.0 + self._jitter()

    # -- state used by the bridge when merging reports ------------------------
    def press(self, keys: Iterable[int]) -> None:
        self.pressed.update(keys)
        self.target.macro_keys_changed()

    def release(self, keys: Iterable[int]) -> None:
        self.pressed.difference_update(keys)
        self.target.macro_keys_changed()

    def release_all(self) -> None:
        self.pressed.clear()
        self.buttons = 0
        self.target.macro_keys_changed()
        self.target.macro_buttons_changed()

    def button(self, bit: int, down: bool) -> None:
        if down:
            self.buttons |= 1 << bit
        else:
            self.buttons &= ~(1 << bit)
        self.target.macro_buttons_changed()

    # -- scheduling -----------------------------------------------------------
    def compile(self, name: str) -> list[Step]:
        if name not in self.macros:
            raise MacroError(f"no such macro: {name}")
        if name not in self._compiled:
            self._compiled[name] = [parse_step(s, self.macros) for s in self.macros[name]]
        return self._compiled[name]

    def start(self, name: str, now: float | None = None) -> None:
        self.start_steps(self.compile(name), label=name, now=now)

    def start_steps(self, steps: list[Step], label: str = "adhoc", now: float | None = None) -> None:
        task = MacroTask(self, label, steps)
        self.running += 1
        log.info("macro %s started (%d steps)", label, len(steps))
        self._advance(task, time.monotonic() if now is None else now)

    def next_deadline(self) -> float | None:
        return self._queue[0].when if self._queue else None

    def run_due(self, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        while self._queue and self._queue[0].when <= now:
            item = heapq.heappop(self._queue)
            self._advance(item.task, now)

    def _advance(self, task: MacroTask, now: float) -> None:
        try:
            delay = next(task.gen)
        except StopIteration:
            task.done = True
            self.running -= 1
            self.completed += 1
            log.info("macro %s finished", task.label)
            return
        except MacroError as exc:
            task.done = True
            self.running -= 1
            self.failed += 1
            log.error("macro %s aborted: %s", task.label, exc)
            self.release_all()
            return
        heapq.heappush(self._queue, _Scheduled(now + max(0.0, delay), next(self._seq), task))

    def stats(self) -> dict:
        return {
            "running": self.running,
            "completed": self.completed,
            "failed": self.failed,
            "keys_held": sorted(self.pressed),
            "buttons_held": self.buttons,
            "defined": sorted(self.macros),
        }
```

## hid_bridge/control.py

`3886 bytes, 114 lines, sha256 1cbd3f1b94681b081dd74048c9ca8aea852487e5228d6f9745acda851b38d5f2`

```python
"""Local control socket (newline-delimited JSON over a Unix stream socket).

Request examples::

    {"cmd": "status"}
    {"cmd": "macro", "name": "login"}
    {"cmd": "steps", "steps": ["ctrl+alt+delete", "wait 500", "type hello"]}
    {"cmd": "type", "text": "hello"}
    {"cmd": "keys", "combo": "ctrl+alt+delete"}
    {"cmd": "release_all"}

Every reply is one JSON object with ``ok`` (bool) and either ``result`` or
``error``.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import stat
from typing import Callable

log = logging.getLogger("hid-bridge.control")

MAX_REQUEST = 64 * 1024


class ControlServer:
    def __init__(self, path: str, handler: Callable[[dict], dict]):
        self.path = path
        self.handler = handler
        self.sock: socket.socket | None = None

    def open(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        try:
            if stat.S_ISSOCK(os.stat(self.path).st_mode):
                os.unlink(self.path)
        except FileNotFoundError:
            pass
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.bind(self.path)
        os.chmod(self.path, 0o660)
        self.sock.listen(8)
        log.info("control socket listening on %s", self.path)

    def fileno(self) -> int:
        assert self.sock is not None
        return self.sock.fileno()

    def close(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        try:
            os.unlink(self.path)
        except OSError:
            pass

    def handle_ready(self) -> None:
        """Accept and service one pending connection (called from the main loop)."""
        assert self.sock is not None
        try:
            conn, _ = self.sock.accept()
        except (BlockingIOError, InterruptedError):
            return
        with conn:
            # Local clients send immediately; never let one hold the main loop.
            conn.settimeout(0.05)
            try:
                chunks = []
                total = 0
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                    if b"\n" in chunk or total > MAX_REQUEST:
                        break
                raw = b"".join(chunks).split(b"\n", 1)[0].decode("utf-8", "replace").strip()
                if not raw:
                    reply = {"ok": False, "error": "empty request"}
                else:
                    try:
                        request = json.loads(raw)
                        if not isinstance(request, dict):
                            raise ValueError("request must be a JSON object")
                        reply = {"ok": True, "result": self.handler(request)}
                    except Exception as exc:  # noqa: BLE001 - reported to the client
                        reply = {"ok": False, "error": str(exc)}
                conn.sendall((json.dumps(reply) + "\n").encode())
            except (socket.timeout, OSError) as exc:
                log.debug("control client error: %s", exc)


def send_request(path: str, request: dict, timeout: float = 5.0) -> dict:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(path)
        sock.sendall((json.dumps(request) + "\n").encode())
        data = b""
        while not data.endswith(b"\n"):
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
    if not data:
        raise ConnectionError("no reply from hid-bridge")
    return json.loads(data.decode())
```

## hid_bridge/bridge.py

`32482 bytes, 737 lines, sha256 5e284780c0214af345143197b48b00b3b7c92e5e789ec801cbb09fd4185c08ba`

```python
"""The bridge daemon: evdev sources in, HID gadget reports out."""
from __future__ import annotations

import logging
import os
import select
import signal
import time
from collections import deque

from . import linux_input as li
from .config import Config, InputRule
from .control import ControlServer
from .descriptors import ABS_MAX_VALUE, KEYBOARD_OUTPUT_LENGTH, KEYBOARD_REPORT_LENGTH, mouse_report_length
from .gadget import udc_current_state, udc_state
from .hidg import HidgDevice
from .keymap import CODE_NAMES, EVDEV_TO_HID, KEY_CODES
from .linux_input import InputDevice, list_event_nodes
from .macros import MacroEngine, MacroError, Step, parse_step
from .reports import (
    BUTTON_BITS,
    KEYBOARD_IDLE_REPORT,
    LED_BIT_TO_EVDEV,
    absolute_mouse_report,
    clamp,
    keyboard_max_array_usage,
    keyboard_report,
    relative_mouse_reports,
    scale_abs,
)

log = logging.getLogger("hid-bridge")


class Source:
    """One attached evdev device and the state it contributes."""

    def __init__(self, dev: InputDevice, rule: InputRule):
        self.dev = dev
        self.rule = rule
        self.role = rule.role
        self.pressed: set[int] = set()
        self.buttons = 0
        self.dx = 0
        self.dy = 0
        self.wheel = 0
        self.abs_x: int | None = None
        self.abs_y: int | None = None
        self.last_px: int | None = None
        self.last_py: int | None = None
        self.mouse_dirty = False
        self.abs_dirty = False
        self.events = 0
        self.attached_at = time.monotonic()
        self.bindings: dict[int, str] = {}
        for key_name, macro_name in rule.bindings.items():
            code = KEY_CODES.get(key_name)
            if code is None:
                log.warning("%s: binding for unknown key %s ignored", dev.name, key_name)
                continue
            self.bindings[code] = macro_name

    def describe(self) -> dict:
        ident = self.dev.identity
        return {
            "path": self.dev.path,
            "name": ident.name,
            "phys": ident.phys,
            "vendor": f"{ident.vendor:04x}",
            "product": f"{ident.product:04x}",
            "keyboard": self.dev.is_keyboard,
            "mouse": self.dev.is_mouse,
            "absolute": self.dev.has_abs_pointer,
            "role": self.role,
            "rule": self.rule.describe(),
            "grabbed": self.dev.grabbed,
            "events": self.events,
            "keys_held": sorted(self.pressed),
            "buttons_held": self.buttons,
        }


class Bridge:
    def __init__(self, cfg: Config, devices: dict):
        self.cfg = cfg
        b = cfg.bridge
        self.kbd = HidgDevice(devices["keyboard"], KEYBOARD_REPORT_LENGTH, "keyboard")
        self.mouse = HidgDevice(devices["mouse"], mouse_report_length(cfg.mouse.mode), "mouse")
        # "Device registers": what the host should receive next.  Key and
        # button *transitions* are kept in short FIFOs so a press that is
        # followed by its release before the host polls is still reported
        # once (a real keyboard's scan buffer does the same); mouse motion
        # accumulates between host polls exactly as a real mouse's counters
        # do and saturates when the host stops collecting.  Nothing blocks.
        self._kbd_queue: deque[bytes] = deque(maxlen=self.TRANSITION_QUEUE)
        self._btn_queue: deque[int] = deque(maxlen=self.TRANSITION_QUEUE)
        self._mouse_dirty = False
        self._mouse_dx = 0
        self._mouse_dy = 0
        self._mouse_wheel = 0
        self._mouse_last_buttons: int | None = None   # None: host state unknown, must send
        self._motion_blocked_since: float | None = None
        self.udc = devices.get("udc", "")
        suspended_path = f"/sys/class/udc/{self.udc}/gadget/suspended" if self.udc else ""
        self.kbd.suspended_path = suspended_path
        self.mouse.suspended_path = suspended_path
        self.sources: dict[int, Source] = {}
        self.by_path: dict[str, Source] = {}
        self.ignored: dict[str, str] = {}
        self.retry_after: dict[str, float] = {}
        self.macro = MacroEngine(self, cfg.macros, b.tap_ms, b.step_ms, b.macro_jitter_ms)
        self.max_usage = keyboard_max_array_usage(cfg.keyboard.descriptor)
        self.abs_pos = [ABS_MAX_VALUE // 2, ABS_MAX_VALUE // 2]
        self.leds = 0
        self.control = ControlServer(b.control_socket, self.handle_control) if b.control_socket else None
        self.stop = False
        self.started = time.monotonic()
        self._wake_r, self._wake_w = os.pipe()
        os.set_blocking(self._wake_r, False)
        os.set_blocking(self._wake_w, False)

    # ------------------------------------------------------------------ state
    def all_usages(self) -> set[int]:
        usages = set(self.macro.pressed)
        for src in self.sources.values():
            usages |= src.pressed
        return usages

    def all_buttons(self) -> int:
        buttons = self.macro.buttons
        for src in self.sources.values():
            buttons |= src.buttons
        return buttons

    MOTION_LIMIT = 4095        # overflow guard for the motion accumulators
    MOTION_SATURATE = 127      # what an 8-bit mouse hands over after the host stopped collecting
    STALL_GAP = 0.1            # host not collecting for this long: saturate like the real counters
    TRANSITION_QUEUE = 16      # key/button states kept while the host is not collecting

    @property
    def _kbd_dirty(self) -> bool:
        return bool(self._kbd_queue)

    def _flush_keyboard(self) -> None:
        report = keyboard_report(self.all_usages(), self.max_usage)
        tail = self._kbd_queue[-1] if self._kbd_queue else self.kbd.last_report
        if tail is None and report == KEYBOARD_IDLE_REPORT:
            # Host state unknown (start-up or re-enumeration) but nothing is
            # held: a real keyboard sends nothing until its state changes,
            # and the host assumes all keys up after enumeration.
            self.kbd.last_report = KEYBOARD_IDLE_REPORT
            return
        if report != tail:
            self._kbd_queue.append(report)
        self._pump_keyboard()

    def _pump_keyboard(self, from_pollout: bool = False) -> None:
        """Deliver queued keyboard states, oldest first, while the host takes them."""
        now = time.monotonic()
        while self._kbd_queue:
            if self.kbd.backoff_until > now:
                return
            if self.kbd.write_report(self._kbd_queue[0]):
                self._kbd_queue.popleft()
                continue
            self._on_write_deferred(self.kbd, from_pollout, now)
            return

    def _note_buttons(self) -> None:
        buttons = self.all_buttons()
        tail = self._btn_queue[-1] if self._btn_queue else self._mouse_last_buttons
        if buttons != tail:
            self._btn_queue.append(buttons)

    def _emit_mouse_motion(self, dx: int, dy: int, wheel: int) -> None:
        self._note_buttons()
        if self.cfg.mouse.mode == "relative":
            self._mouse_dx = clamp(self._mouse_dx + dx, -self.MOTION_LIMIT, self.MOTION_LIMIT)
            self._mouse_dy = clamp(self._mouse_dy + dy, -self.MOTION_LIMIT, self.MOTION_LIMIT)
        elif dx or dy:
            gain = self.cfg.mouse.rel_to_abs_gain
            self.abs_pos[0] = clamp(self.abs_pos[0] + round(dx * gain), 0, ABS_MAX_VALUE)
            self.abs_pos[1] = clamp(self.abs_pos[1] + round(dy * gain), 0, ABS_MAX_VALUE)
        self._mouse_wheel = clamp(self._mouse_wheel + wheel, -self.MOTION_LIMIT, self.MOTION_LIMIT)
        self._mouse_dirty = True
        self._pump_mouse()

    def _emit_mouse_absolute(self, x: int | None, y: int | None, wheel: int) -> None:
        self._note_buttons()
        if x is not None:
            self.abs_pos[0] = x
        if y is not None:
            self.abs_pos[1] = y
        self._mouse_wheel = clamp(self._mouse_wheel + wheel, -self.MOTION_LIMIT, self.MOTION_LIMIT)
        self._mouse_dirty = True
        self._pump_mouse()

    def _motion_pending(self) -> bool:
        return bool(self._mouse_dx or self._mouse_dy or self._mouse_wheel)

    def _drop_motion(self) -> None:
        self._mouse_dx = self._mouse_dy = self._mouse_wheel = 0
        self._motion_blocked_since = None

    def _saturate_motion(self) -> None:
        lim = self.MOTION_SATURATE
        self._mouse_dx = clamp(self._mouse_dx, -lim, lim)
        self._mouse_dy = clamp(self._mouse_dy, -lim, lim)
        self._mouse_wheel = clamp(self._mouse_wheel, -lim, lim)

    def _on_write_deferred(self, sink: HidgDevice, from_pollout: bool, now: float) -> None:
        """A write could not be handed to the kernel right now."""
        if sink.disconnected or sink.host_disabled:
            if sink is self.mouse:
                self._drop_motion()      # no host to deliver motion to; buttons kept
            return
        if sink is self.mouse and self._motion_pending() and self._motion_blocked_since is None:
            self._motion_blocked_since = now
        if from_pollout:
            # Writable yet refused: the bus is suspended and dwc2 rejects
            # requests until the host resumes.  Retry with backoff; motion
            # gathered while asleep is meaningless, as on a real mouse.
            sink.enter_backoff(now)
            self._drop_motion()

    def _pump_mouse(self, from_pollout: bool = False) -> None:
        """Send pending mouse state, one report per host poll slot."""
        n = self.cfg.mouse.buttons
        relative = self.cfg.mouse.mode == "relative"
        now = time.monotonic()
        while True:
            if self.mouse.backoff_until > now:
                return
            if self.mouse.last_report is None:
                self._mouse_last_buttons = None          # host re-enumerated: its state is unknown
            if (self._mouse_last_buttons is None and not self._btn_queue and not self._motion_pending()
                    and self.all_buttons() == 0):
                # Nothing held and nothing to move: the host assumes all
                # buttons up after enumeration; say nothing, as a mouse does.
                self._mouse_last_buttons = 0
                self._mouse_dirty = False
                return
            if self._motion_blocked_since is not None and now - self._motion_blocked_since > self.STALL_GAP:
                self._saturate_motion()
            if self._btn_queue:
                buttons = self._btn_queue[0]
            elif self._mouse_last_buttons is not None:
                buttons = self._mouse_last_buttons
            else:
                buttons = self.all_buttons()
            cw = clamp(self._mouse_wheel, -127, 127)
            if relative:
                cx = clamp(self._mouse_dx, -127, 127)
                cy = clamp(self._mouse_dy, -127, 127)
                must_send = bool(self._btn_queue) or bool(cx or cy or cw) or self._mouse_last_buttons is None
                report = relative_mouse_reports(buttons, cx, cy, cw, n)[0]
                # GET_REPORT on a relative mouse answers buttons with zero motion.
                still = relative_mouse_reports(buttons, 0, 0, 0, n)[0]
            else:
                cx = cy = 0
                x, y = self.abs_pos
                report = absolute_mouse_report(buttons, x, y, cw, n)
                still = absolute_mouse_report(buttons, x, y, 0, n)
                must_send = bool(self._btn_queue) or bool(cw) or report != self.mouse.last_report
            if not must_send:
                self._mouse_dirty = False
                return
            if not self.mouse.write_report(report, force=True, get_report=still):
                self._on_write_deferred(self.mouse, from_pollout, now)
                return
            if self._btn_queue:
                self._btn_queue.popleft()
            self._mouse_last_buttons = buttons
            self._mouse_dx -= cx
            self._mouse_dy -= cy
            self._mouse_wheel -= cw
            self._motion_blocked_since = None
            self._mouse_dirty = bool(self._btn_queue) or self._motion_pending()
            if not self._mouse_dirty:
                return

    def _resync_source(self, src: Source) -> None:
        """The kernel dropped events for this device: rebuild its state from EVIOCGKEY."""
        held = src.dev.active_keys()
        drop = src.role == "macro" and src.rule.unbound == "drop"
        src.pressed = set()
        src.buttons = 0
        if not drop:
            for code in held:
                if code in src.bindings:
                    continue
                if code >= li.BTN_MOUSE:
                    bit = BUTTON_BITS.get(code)
                    if bit is not None:
                        src.buttons |= 1 << bit
                else:
                    usage = EVDEV_TO_HID.get(code)
                    if usage is not None:
                        src.pressed.add(usage)
        src.dx = src.dy = src.wheel = 0
        src.mouse_dirty = src.abs_dirty = False
        log.warning("%s: events dropped by the kernel; state resynchronised (%d keys held)", src.dev.name, len(src.pressed))
        self._flush_keyboard()
        self._emit_mouse_motion(0, 0, 0)

    # ----------------------------------------------------------- MacroTarget
    def macro_keys_changed(self) -> None:
        self._flush_keyboard()

    def macro_mouse_move(self, dx: int, dy: int, wheel: int) -> None:
        self._emit_mouse_motion(dx, dy, wheel)

    def macro_mouse_to(self, x: int, y: int) -> None:
        if self.cfg.mouse.mode != "absolute":
            log.warning("'mouse to' needs mouse.mode = \"absolute\"; step ignored")
            return
        self._emit_mouse_absolute(clamp(x, 0, ABS_MAX_VALUE), clamp(y, 0, ABS_MAX_VALUE), 0)

    def macro_buttons_changed(self) -> None:
        self._emit_mouse_motion(0, 0, 0)

    # --------------------------------------------------------------- sources
    def _rescan(self) -> None:
        now = time.monotonic()
        present = set(list_event_nodes())
        for path in list(self.ignored):
            if path not in present:
                del self.ignored[path]
                continue
            # udev reuses eventN numbers: a different device on the same
            # path must be re-evaluated, not inherit the old verdict.
            reason, inode = self.ignored[path]
            try:
                if os.stat(path).st_ino != inode:
                    del self.ignored[path]
            except OSError:
                del self.ignored[path]
        for path in list(self.retry_after):
            if path not in present:
                del self.retry_after[path]
        for path in sorted(present):
            if path in self.by_path or path in self.ignored:
                continue
            if self.retry_after.get(path, 0) > now:
                continue
            try:
                dev = InputDevice(path)
            except OSError as exc:
                self.retry_after[path] = now + 5.0
                log.debug("%s: cannot open (%s); will retry", path, exc.strerror)
                continue
            ident = dev.identity
            rule = self.cfg.rule_for(ident.name, ident.phys, ident.vendor, ident.product)
            if rule.role == "ignore":
                self.ignored[path] = (f"rule {rule.describe()}", self._inode(path))
                log.info("%s (%s) ignored by rule %s", path, ident.name, rule.describe())
                dev.close()
                continue
            if not (dev.is_keyboard or dev.is_mouse):
                self.ignored[path] = ("not a keyboard or mouse", self._inode(path))
                log.debug("%s (%s) is neither keyboard nor mouse; ignored", path, ident.name)
                dev.close()
                continue
            grab = self.cfg.bridge.grab_inputs if rule.grab is None else rule.grab
            if grab:
                try:
                    dev.grab()
                except OSError as exc:
                    log.warning("%s (%s): cannot grab: %s", path, ident.name, exc.strerror)
            src = Source(dev, rule)
            self.sources[dev.fd] = src
            self.by_path[path] = src
            self._apply_leds(src)
            log.info(
                "attached %s: %r [%04x:%04x] kbd=%s mouse=%s abs=%s role=%s (%s)%s",
                path, ident.name, ident.vendor, ident.product, dev.is_keyboard, dev.is_mouse,
                dev.has_abs_pointer, src.role, rule.describe(), " grabbed" if dev.grabbed else "",
            )

    @staticmethod
    def _inode(path: str) -> int:
        try:
            return os.stat(path).st_ino
        except OSError:
            return 0

    def _remove_source(self, src: Source, reason: str) -> None:
        log.info("detached %s (%r): %s", src.dev.path, src.dev.name, reason)
        self.sources.pop(src.dev.fd, None)
        self.by_path.pop(src.dev.path, None)
        had_keys = bool(src.pressed)
        had_buttons = bool(src.buttons)
        src.pressed.clear()
        src.buttons = 0
        src.dev.close()
        if had_keys:
            self._flush_keyboard()
        if had_buttons:
            self._emit_mouse_motion(0, 0, 0)

    def _apply_leds(self, src: Source) -> None:
        if not self.cfg.bridge.forward_leds or not src.dev.is_keyboard:
            return
        for bit, led in LED_BIT_TO_EVDEV.items():
            src.dev.set_led(led, bool(self.leds & (1 << bit)))

    def _handle_leds(self) -> None:
        data = self.kbd.read_output_report()
        if not data:
            return
        if len(data) != KEYBOARD_OUTPUT_LENGTH:
            # Only the 1-byte LED Output report exists.  Anything else is a
            # SET_REPORT of another type that an unpatched usb_f_hid let
            # through (kernel-patches/0003 makes the kernel STALL it).
            log.debug("ignoring %d-byte SET_REPORT that is not the LED report", len(data))
            return
        leds = data[0]
        if leds == self.leds:
            return
        self.leds = leds
        log.debug("LED state from host: 0x%02x", leds)
        for src in self.sources.values():
            self._apply_leds(src)

    # ---------------------------------------------------------------- events
    def _process(self, src: Source) -> None:
        try:
            events = src.dev.read_events()
        except OSError as exc:
            self._remove_source(src, exc.strerror or "read error")
            return
        kbd_changed = False
        drop_unbound = src.role == "macro" and src.rule.unbound == "drop"
        for ev_type, code, value in events:
            src.events += 1
            if ev_type == li.EV_KEY:
                if value == 2:
                    continue  # autorepeat: the host generates its own
                if src.role == "macro" and code in src.bindings:
                    if value == 1:
                        name = src.bindings[code]
                        try:
                            self.macro.start(name)
                        except MacroError as exc:
                            log.error("binding %s -> %s: %s", CODE_NAMES.get(code, code), name, exc)
                    continue
                if drop_unbound:
                    continue
                if code >= li.BTN_MOUSE:
                    bit = BUTTON_BITS.get(code)
                    if bit is None:
                        continue
                    if value:
                        src.buttons |= 1 << bit
                    else:
                        src.buttons &= ~(1 << bit)
                    src.mouse_dirty = True
                else:
                    usage = EVDEV_TO_HID.get(code)
                    if usage is None:
                        log.debug("%s: no HID usage for %s", src.dev.name, CODE_NAMES.get(code, code))
                        continue
                    if value:
                        src.pressed.add(usage)
                    else:
                        src.pressed.discard(usage)
                    kbd_changed = True
            elif ev_type == li.EV_REL:
                if drop_unbound:
                    continue
                if code == li.REL_X:
                    src.dx += value
                elif code == li.REL_Y:
                    src.dy += value
                elif code == li.REL_WHEEL:
                    src.wheel += value
                else:
                    continue  # HWHEEL and hi-res variants are not in the descriptor
                src.mouse_dirty = True
            elif ev_type == li.EV_ABS:
                if drop_unbound:
                    continue
                if code == li.ABS_X:
                    src.abs_x = value
                elif code == li.ABS_Y:
                    src.abs_y = value
                else:
                    continue
                src.abs_dirty = True
            elif ev_type == li.EV_SYN and code == li.SYN_REPORT:
                if kbd_changed:
                    self._flush_keyboard()
                    kbd_changed = False
                if src.mouse_dirty or src.abs_dirty:
                    self._flush_source_mouse(src)
            elif ev_type == li.EV_SYN and code == li.SYN_DROPPED:
                self._resync_source(src)
                kbd_changed = False
        if kbd_changed:
            self._flush_keyboard()

    def _flush_source_mouse(self, src: Source) -> None:
        dx, dy, wheel = src.dx, src.dy, src.wheel
        src.dx = src.dy = src.wheel = 0
        src.mouse_dirty = False
        if src.abs_dirty and src.dev.has_abs_pointer:
            src.abs_dirty = False
            ax = src.dev.absinfo[li.ABS_X]
            ay = src.dev.absinfo[li.ABS_Y]
            if self.cfg.mouse.mode == "absolute":
                x = scale_abs(src.abs_x, ax.minimum, ax.span) if src.abs_x is not None else None
                y = scale_abs(src.abs_y, ay.minimum, ay.span) if src.abs_y is not None else None
                self._emit_mouse_absolute(x, y, wheel)
                return
            # Absolute source, relative output: convert to deltas on a virtual screen.
            width, height = self.cfg.mouse.abs_to_rel_resolution
            if src.abs_x is not None and src.abs_y is not None:
                px = scale_abs(src.abs_x, ax.minimum, ax.span, width - 1)
                py = scale_abs(src.abs_y, ay.minimum, ay.span, height - 1)
                if src.last_px is not None and src.last_py is not None:
                    dx += px - src.last_px
                    dy += py - src.last_py
                src.last_px, src.last_py = px, py
        src.abs_dirty = False
        self._emit_mouse_motion(dx, dy, wheel)

    # --------------------------------------------------------------- control
    def handle_control(self, request: dict) -> dict:
        cmd = request.get("cmd")
        if cmd == "status":
            return self.status()
        if cmd == "inputs":
            return {"sources": [s.describe() for s in self.sources.values()],
                    "ignored": {path: reason for path, (reason, _inode) in self.ignored.items()}}
        if cmd == "macro":
            name = str(request.get("name", ""))
            self.macro.start(name)
            return {"started": name}
        if cmd == "steps":
            raw = request.get("steps")
            if not isinstance(raw, list) or not raw:
                raise ValueError("'steps' must be a non-empty list of step strings")
            steps = [parse_step(str(s), self.cfg.macros) for s in raw]
            self.macro.start_steps(steps, label="ctl")
            return {"started": [s.describe() for s in steps]}
        if cmd == "type":
            text = str(request.get("text", ""))
            self.macro.start_steps([Step("type", text=text)], label="ctl-type")
            return {"typing": len(text)}
        if cmd == "keys":
            step = parse_step(str(request.get("combo", "")), self.cfg.macros)
            self.macro.start_steps([step], label="ctl-keys")
            return {"started": step.describe()}
        if cmd == "release_all":
            self.macro.release_all()
            for src in self.sources.values():
                src.pressed.clear()
                src.buttons = 0
            self._flush_keyboard()
            self._emit_mouse_motion(0, 0, 0)
            return {"released": True}
        raise ValueError(f"unknown command {cmd!r}")

    def _poll_host_state(self) -> None:
        for sink in (self.kbd, self.mouse):
            sink.revalidate()
        if not self.udc:
            return
        was_away = self.kbd.host_disabled or self.mouse.host_disabled
        state = udc_current_state(self.udc)
        self.kbd.host_state_changed(state)
        self.mouse.host_state_changed(state)
        if was_away and state == "configured":
            # Re-sync the host with the current state after it came back.
            self.kbd.last_report = None
            self.mouse.last_report = None
            self._flush_keyboard()
            self._mouse_dirty = True
        self._pump_keyboard()
        self._pump_mouse()

    def _service_backoff(self, now: float) -> float | None:
        """Retry sinks whose backoff expired; return the next wake-up time."""
        next_wake = None
        for sink, dirty, pump in ((self.kbd, self._kbd_dirty, self._pump_keyboard),
                                  (self.mouse, self._mouse_dirty, self._pump_mouse)):
            if not dirty or not sink.backoff_until:
                continue
            if sink.backoff_until > now:
                next_wake = sink.backoff_until if next_wake is None else min(next_wake, sink.backoff_until)
                continue
            if sink.host_suspended():
                sink.extend_backoff(now)            # still asleep: do not even try
                next_wake = sink.backoff_until if next_wake is None else min(next_wake, sink.backoff_until)
                continue
            sink.backoff_until = 0.0
            pump()
            if sink.backoff_until:
                next_wake = sink.backoff_until if next_wake is None else min(next_wake, sink.backoff_until)
        return next_wake

    def status(self) -> dict:
        return {
            "uptime_s": round(time.monotonic() - self.started, 1),
            "udc": udc_state(self.udc) if self.udc else {},
            "keyboard": self.kbd.stats(),
            "mouse": {**self.mouse.stats(), "mode": self.cfg.mouse.mode, "buttons": self.cfg.mouse.buttons},
            "leds": self.leds,
            "keys_held": sorted(self.all_usages()),
            "buttons_held": self.all_buttons(),
            "sources": [s.describe() for s in self.sources.values()],
            "macros": self.macro.stats(),
        }

    # ------------------------------------------------------------------ loop
    def _on_signal(self, signum, _frame) -> None:
        self.stop = True
        try:
            os.write(self._wake_w, b"x")
        except OSError:
            pass

    def run(self) -> None:
        signal.signal(signal.SIGTERM, self._on_signal)
        signal.signal(signal.SIGINT, self._on_signal)
        signal.signal(signal.SIGHUP, self._on_signal)
        self.kbd.open()
        self.mouse.open()
        if self.control is not None:
            try:
                self.control.open()
            except OSError as exc:
                log.warning("control socket unavailable: %s", exc)
                self.control = None
        # No unsolicited report at start: a real keyboard sends nothing until
        # its state changes.  open() has primed the GET_REPORT cache already.
        log.info("bridge running: keyboard=%s mouse=%s (%s, %d buttons), sources rescanned every %d ms",
                 self.kbd.path, self.mouse.path, self.cfg.mouse.mode, self.cfg.mouse.buttons,
                 self.cfg.bridge.rescan_interval_ms)
        rescan_every = self.cfg.bridge.rescan_interval_ms / 1000.0
        next_rescan = 0.0
        try:
            while not self.stop:
                now = time.monotonic()
                if now >= next_rescan:
                    self._rescan()
                    self._poll_host_state()
                    next_rescan = now + rescan_every
                self.macro.run_due(now)
                timeout = next_rescan - now
                deadline = self.macro.next_deadline()
                if deadline is not None:
                    timeout = min(timeout, deadline - now)
                wake = self._service_backoff(now)
                if wake is not None:
                    timeout = min(timeout, wake - now)
                timeout = max(0.0, timeout)
                rlist = list(self.sources) + [self._wake_r]
                if self.kbd.poll_readable:
                    rlist.append(self.kbd.fd)
                if self.control is not None:
                    rlist.append(self.control.fileno())
                # usb_f_hid reports POLLOUT once the host has collected the
                # previous report; that is when pending state goes out.
                wlist = []
                if self._kbd_dirty and self.kbd.fd >= 0 and not self.kbd.backoff_until:
                    wlist.append(self.kbd.fd)
                if self._mouse_dirty and self.mouse.fd >= 0 and not self.mouse.backoff_until:
                    wlist.append(self.mouse.fd)
                try:
                    readable, writable, _ = select.select(rlist, wlist, [], timeout)
                except InterruptedError:
                    continue
                except OSError as exc:
                    # A source vanished between rescan and select: drop dead fds.
                    log.debug("select: %s; pruning sources", exc.strerror)
                    for fd, src in list(self.sources.items()):
                        try:
                            os.fstat(fd)
                        except OSError:
                            self._remove_source(src, "fd closed")
                    continue
                for fd in writable:
                    if fd == self.kbd.fd:
                        self._pump_keyboard(from_pollout=True)
                    elif fd == self.mouse.fd:
                        self._pump_mouse(from_pollout=True)
                for fd in readable:
                    if fd == self._wake_r:
                        try:
                            os.read(self._wake_r, 64)
                        except OSError:
                            pass
                    elif fd == self.kbd.fd:
                        self._handle_leds()
                    elif self.control is not None and fd == self.control.fileno():
                        self.control.handle_ready()
                    elif fd in self.sources:
                        self._process(self.sources[fd])
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        held_keys = bool(self.all_usages())
        held_buttons = bool(self.all_buttons())
        log.info("shutting down%s", ": releasing held keys/buttons" if held_keys or held_buttons else "")
        self.macro.pressed.clear()
        self.macro.buttons = 0
        for src in list(self.sources.values()):
            src.pressed.clear()
            src.buttons = 0
        self._drop_motion()
        self._kbd_queue.clear()
        self._btn_queue.clear()
        # A real keyboard sends nothing when nothing changes; only release
        # what was held, and wait briefly for the host to collect it so a
        # restart never leaves a key auto-repeating on the target.
        try:
            if held_keys:
                self.kbd.write_report_blocking(bytes(KEYBOARD_REPORT_LENGTH), 0.1)
            if held_buttons:
                n = self.cfg.mouse.buttons
                if self.cfg.mouse.mode == "relative":
                    report = relative_mouse_reports(0, 0, 0, 0, n)[0]
                else:
                    report = absolute_mouse_report(0, self.abs_pos[0], self.abs_pos[1], 0, n)
                self.mouse.write_report_blocking(report, 0.1)
        except Exception as exc:  # noqa: BLE001
            log.debug("final reports not delivered: %s", exc)
        for src in list(self.sources.values()):
            src.dev.close()
        self.sources.clear()
        self.by_path.clear()
        if self.control is not None:
            self.control.close()
        self.kbd.close()
        self.mouse.close()
```

## tests/__init__.py

`0 bytes, 0 lines, sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

```python
```

## tests/test_bridge.py

`24309 bytes, 554 lines, sha256 208a7ef40ec55792892c097bdad6daf6742659fe7f8faf64b6ef0f1b86aee257`

```python
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
        self.suspended = False  # True = bus suspended: writable but every write is refused
        self.backoff_until = 0.0
        self.backoffs = 0
        self.last_sent_at = 0.0
        self.suspended_path = ""
        self.blocking_writes = []

    def write_report(self, report, force=False, get_report=None):
        assert len(report) == self.report_length
        cache = report if get_report is None else get_report
        if not self.get_reports or self.get_reports[-1] != cache:
            self.get_reports.append(bytes(cache))
        if not force and report == self.last_report:
            return True
        if not self.writable or self.disconnected or self.suspended:
            return False
        self.reports.append(bytes(report))
        self.last_report = bytes(report)
        self.backoff_until = 0.0
        return True

    def write_report_blocking(self, report, timeout):
        self.blocking_writes.append(bytes(report))
        return self.write_report(report, force=True)

    def revalidate(self):
        return False

    def host_suspended(self):
        return self.suspended

    def enter_backoff(self, now):
        self.backoffs += 1
        self.backoff_until = now + 0.05

    def extend_backoff(self, now, seconds=0.25):
        self.backoff_until = now + seconds

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
        self.held = set()   # what EVIOCGKEY would report
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

    def active_keys(self):
        return set(self.held)

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
        # modifiers lead in their own report, then the key joins them
        self.assertEqual(bridge.kbd.reports, [bytes([0x05, 0, 0, 0, 0, 0, 0, 0])])
        bridge.macro.run_due(bridge.macro.next_deadline())
        self.assertEqual(bridge.kbd.reports[-1], bytes([0x05, 0, 0x4C, 0, 0, 0, 0, 0]))
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
        # every transition is replayed in order, the final state is idle
        self.assertEqual(bridge.kbd.reports[1:], [bytes(8), bytes([0, 0, 0x05, 0, 0, 0, 0, 0]), bytes(8)])
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
        # the click happened: press then release are both delivered, in order
        self.assertEqual(bridge.mouse.reports, [bytes([1, 0, 0, 0]), bytes([0, 0, 0, 0])])
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


class SuspendAndRobustnessTests(unittest.TestCase):
    def test_suspended_bus_backs_off_instead_of_spinning(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("K", keyboard=True, mouse=True))
        bridge.kbd.suspended = True
        bridge.mouse.suspended = True
        src.dev.queue = [key("KEY_A", 1), (li.EV_REL, li.REL_X, 30), SYN]
        bridge._process(src)                          # first attempt: looks like "in flight"
        self.assertEqual(bridge.kbd.backoffs, 0)
        bridge._pump_keyboard(from_pollout=True)      # POLLOUT said writable, write still refused
        bridge._pump_mouse(from_pollout=True)
        self.assertEqual((bridge.kbd.backoffs, bridge.mouse.backoffs), (1, 1))
        self.assertGreater(bridge.kbd.backoff_until, 0)
        self.assertEqual((bridge._mouse_dx, bridge._mouse_dy), (0, 0))   # motion while asleep is discarded
        self.assertTrue(bridge._kbd_dirty)             # the key state is kept for the resume
        # while backing off, the loop must not select() on the fd
        bridge._pump_keyboard()
        self.assertEqual(len(bridge.kbd.reports), 0)
        # host resumes
        bridge.kbd.suspended = bridge.mouse.suspended = False
        bridge.kbd.backoff_until = bridge.mouse.backoff_until = 0.0
        bridge._pump_keyboard()
        self.assertEqual(bridge.kbd.reports[-1][2], 0x04)

    def test_service_backoff_waits_while_sysfs_says_suspended(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice())
        src.dev.queue = [key("KEY_A", 1), SYN]
        bridge.kbd.suspended = True
        bridge._process(src)
        bridge._pump_keyboard(from_pollout=True)
        now = bridge.kbd.backoff_until + 1.0
        wake = bridge._service_backoff(now)
        self.assertIsNotNone(wake)
        self.assertGreater(wake, now)                  # extended without a write attempt
        self.assertEqual(bridge.kbd.reports, [])
        bridge.kbd.suspended = False
        now = bridge.kbd.backoff_until + 1.0
        self.assertIsNone(bridge._service_backoff(now))
        self.assertEqual(bridge.kbd.reports[-1][2], 0x04)

    def test_motion_saturates_after_host_stall(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        bridge.mouse.writable = False
        src.dev.queue = [(li.EV_REL, li.REL_X, 300), SYN]
        bridge._process(src)
        bridge._motion_blocked_since -= 1.0             # the host did not collect for a second
        bridge.mouse.writable = True
        bridge._pump_mouse()
        self.assertEqual(bridge.mouse.reports, [bytes([0, 127, 0, 0])])   # one saturated report, like an 8-bit mouse

    def test_syn_dropped_resyncs_from_kernel_state(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("K", keyboard=True, mouse=True))
        src.dev.queue = [key("KEY_A", 1), (li.EV_KEY, li.BTN_LEFT, 1), SYN]
        bridge._process(src)
        src.dev.held = {KEY_CODES["KEY_B"]}            # the kernel says: only B is down now
        src.dev.queue = [(li.EV_SYN, li.SYN_DROPPED, 0)]
        bridge._process(src)
        self.assertEqual(src.pressed, {0x05})
        self.assertEqual(src.buttons, 0)
        self.assertEqual(bridge.kbd.reports[-1][2], 0x05)
        self.assertEqual(bridge.mouse.reports[-1], bytes(4))

    def test_no_unsolicited_reports_at_shutdown_when_idle(self):
        bridge = make_bridge()
        attach(bridge, FakeDevice())
        bridge.shutdown()
        self.assertEqual(bridge.kbd.blocking_writes, [])
        self.assertEqual(bridge.mouse.blocking_writes, [])

    def test_nothing_sent_at_start_or_reenumeration_when_idle(self):
        bridge = make_bridge()
        bridge.kbd.last_report = None          # as at start-up
        attach(bridge, FakeDevice("K", keyboard=True, mouse=True))
        bridge._flush_keyboard()
        bridge._mouse_dirty = True
        bridge._pump_mouse()
        self.assertEqual(bridge.kbd.reports, [])
        self.assertEqual(bridge.mouse.reports, [])
        self.assertEqual(bridge.kbd.last_report, bytes(8))   # host assumed idle
        self.assertEqual(bridge._mouse_last_buttons, 0)

    def test_mouse_resync_after_reenumeration(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("M", keyboard=False, mouse=True))
        src.dev.queue = [(li.EV_KEY, li.BTN_LEFT, 1), SYN]
        bridge._process(src)
        bridge.mouse.last_report = None                 # host reset: it forgot the button
        bridge._mouse_dirty = True
        bridge._pump_mouse()
        self.assertEqual(bridge.mouse.reports[-1], bytes([1, 0, 0, 0]))   # re-asserted


class ShutdownTests(unittest.TestCase):
    def test_shutdown_releases_everything(self):
        bridge = make_bridge()
        src = attach(bridge, FakeDevice("K", keyboard=True, mouse=True))
        src.dev.queue = [key("KEY_A", 1), (li.EV_KEY, li.BTN_LEFT, 1), SYN]
        bridge._process(src)
        bridge.shutdown()
        self.assertEqual(bridge.kbd.blocking_writes, [bytes(8)])
        self.assertEqual(bridge.mouse.blocking_writes, [bytes(4)])
        self.assertTrue(src.dev.closed)
        self.assertEqual(bridge.sources, {})


if __name__ == "__main__":
    unittest.main()
```

## tests/test_config.py

`3436 bytes, 85 lines, sha256 a6bc44645d4a375d79be369445268c7383e48d3bdd2d3bbcc1427c859a17c85a`

```python
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
```

## tests/test_descriptors.py

`2537 bytes, 67 lines, sha256 03da08b336afa256ff782696fe8cb276fea93e0f6d6a558e6459d719923d9546`

```python
import unittest

from hid_bridge.descriptors import (
    KEYBOARD_REPORT_LENGTH,
    keyboard_report_descriptor,
    mouse_report_descriptor,
    mouse_report_length,
    report_bit_sizes,
)

# HID 1.11 Appendix E.6 boot keyboard descriptor, byte for byte.
SPEC_BOOT_KEYBOARD = bytes.fromhex(
    "05010906a101050719e029e71500250175019508810295017508810195057501"
    "050819012905910295017503910195067508150025650507190029658100c0"
)


class DescriptorTests(unittest.TestCase):
    def test_boot_keyboard_matches_spec(self):
        desc = keyboard_report_descriptor(extended=False)
        self.assertEqual(len(desc), 63)
        self.assertEqual(desc, SPEC_BOOT_KEYBOARD)

    def test_keyboard_report_sizes(self):
        for extended in (False, True):
            in_bits, out_bits = report_bit_sizes(keyboard_report_descriptor(extended))
            self.assertEqual(in_bits, KEYBOARD_REPORT_LENGTH * 8)
            self.assertEqual(out_bits, 8)

    def test_extended_keyboard_widens_array(self):
        desc = keyboard_report_descriptor(extended=True)
        self.assertIn(bytes([0x26, 0xFF, 0x00]), desc)
        self.assertIn(bytes([0x2A, 0xFF, 0x00]), desc)
        self.assertEqual(len(desc), 65)

    def test_mouse_relative(self):
        for buttons in (3, 5):
            desc = mouse_report_descriptor("relative", buttons)
            in_bits, out_bits = report_bit_sizes(desc)
            self.assertEqual(in_bits, mouse_report_length("relative") * 8)
            self.assertEqual(out_bits, 0)
            # boot mouse compatible: first three bytes are buttons, X, Y
            self.assertEqual(desc[:6], bytes([0x05, 0x01, 0x09, 0x02, 0xA1, 0x01]))

    def test_mouse_absolute(self):
        desc = mouse_report_descriptor("absolute", 3)
        in_bits, _ = report_bit_sizes(desc)
        self.assertEqual(in_bits, mouse_report_length("absolute") * 8)
        self.assertIn(bytes([0x26, 0xFF, 0x7F]), desc)

    def test_bad_arguments(self):
        with self.assertRaises(ValueError):
            mouse_report_descriptor("relative", 4)
        with self.assertRaises(ValueError):
            mouse_report_descriptor("hover", 3)
        with self.assertRaises(ValueError):
            mouse_report_length("hover")

    def test_parser_rejects_report_ids(self):
        with self.assertRaises(ValueError):
            report_bit_sizes(bytes([0x85, 0x01]))
        with self.assertRaises(ValueError):
            report_bit_sizes(bytes([0xA1, 0x01]))  # unbalanced


if __name__ == "__main__":
    unittest.main()
```

## tests/test_gadget.py

`6163 bytes, 124 lines, sha256 c6d2b179dcb20bd51b8213ef1f5adec2c4976c1091ab7ad6ebf0c50c1cce0bc4`

```python
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
```

## tests/test_hidg.py

`4955 bytes, 123 lines, sha256 2b87c9f9054f3bd62926ac9295284aafec8e0a00f7fc118e849e5204f9ed8300`

```python
import errno
import os
import unittest
from unittest import mock

from hid_bridge import hidg
from hid_bridge.hidg import GADGET_HID_WRITE_GET_REPORT, USB_HIDG_REPORT, HidgDevice


class HidgIoctlTests(unittest.TestCase):
    def test_struct_and_ioctl_number(self):
        # sizeof(struct usb_hidg_report) == 72 -> _IOW('g', 0x42, 72)
        self.assertEqual(USB_HIDG_REPORT.size, 72)
        self.assertEqual(GADGET_HID_WRITE_GET_REPORT, 0x40486742)

    def test_cache_get_report_payload(self):
        dev = HidgDevice("/dev/null", 8, "kbd")
        calls = []

        def fake_ioctl(fd, request, payload):
            calls.append((request, bytes(payload)))
            return 0

        with mock.patch.object(hidg.fcntl, "ioctl", side_effect=fake_ioctl):
            dev.open()
            report = bytes([0x02, 0, 0x04, 0, 0, 0, 0, 0])
            dev.write_report(report)
            dev.write_report(report)  # identical: no second ioctl
        try:
            self.assertEqual(len(calls), 2)  # idle report at open + one update
            request, payload = calls[1]
            self.assertEqual(request, GADGET_HID_WRITE_GET_REPORT)
            report_id, userspace_req, length, data, padding = USB_HIDG_REPORT.unpack(payload)
            self.assertEqual((report_id, userspace_req, length), (0, 0, 8))
            self.assertEqual(data[:8], report)
            self.assertEqual(data[8:], bytes(56))
            self.assertEqual(dev.stats()["get_report_cache"], True)
        finally:
            dev.close()

    def test_cache_disabled_on_old_kernel(self):
        dev = HidgDevice("/dev/null", 4, "mouse")
        with mock.patch.object(hidg.fcntl, "ioctl", side_effect=OSError(errno.ENOTTY, "no ioctl")) as ioctl:
            dev.open()
            dev.write_report(bytes([1, 0, 0, 0]))
            dev.write_report(bytes([0, 0, 0, 0]))
        try:
            self.assertEqual(ioctl.call_count, 1)
            self.assertFalse(dev.stats()["get_report_cache"])
        finally:
            dev.close()


class HidgHostStateTests(unittest.TestCase):
    def make(self):
        dev = HidgDevice("/dev/null", 8, "kbd")
        with mock.patch.object(hidg.fcntl, "ioctl", side_effect=OSError(errno.ENOTTY, "x")):
            dev.open()
        self.addCleanup(dev.close)
        return dev

    def test_dedup_and_force(self):
        dev = self.make()
        r = bytes([0, 0, 4, 0, 0, 0, 0, 0])
        self.assertTrue(dev.write_report(r))
        self.assertTrue(dev.write_report(r))
        self.assertEqual(dev.sent, 1)
        self.assertTrue(dev.write_report(r, force=True))
        self.assertEqual(dev.sent, 2)
        with self.assertRaises(ValueError):
            dev.write_report(bytes(3))

    def test_disabled_function_stops_read_polling(self):
        dev = self.make()
        self.assertTrue(dev.poll_readable)
        with mock.patch.object(hidg.os, "read", side_effect=OSError(errno.ENOMEM, "disabled")):
            self.assertIsNone(dev.read_output_report())
        self.assertTrue(dev.host_disabled)
        self.assertFalse(dev.poll_readable)
        self.assertFalse(dev.stats()["host_connected"])
        dev.host_state_changed("default")
        self.assertFalse(dev.poll_readable)
        dev.host_state_changed("configured")
        self.assertTrue(dev.poll_readable)

    def test_successful_write_clears_disabled(self):
        dev = self.make()
        dev.host_disabled = True
        dev.write_report(bytes([0, 0, 4, 0, 0, 0, 0, 0]))
        self.assertFalse(dev.host_disabled)

    def test_eagain_defers_without_dropping(self):
        dev = self.make()
        with mock.patch.object(hidg.os, "write", side_effect=BlockingIOError()):
            self.assertFalse(dev.write_report(bytes([0, 0, 4, 0, 0, 0, 0, 0])))
        self.assertEqual((dev.deferred, dev.dropped, dev.sent), (1, 0, 0))
        self.assertIsNone(dev.last_report)
        self.assertFalse(dev.disconnected)

    def test_eshutdown_is_a_disconnect(self):
        dev = self.make()
        with mock.patch.object(hidg.os, "write", side_effect=OSError(errno.ESHUTDOWN, "shutdown")):
            self.assertFalse(dev.write_report(bytes([0, 0, 4, 0, 0, 0, 0, 0])))
        self.assertTrue(dev.disconnected)
        self.assertEqual(dev.dropped, 1)
        self.assertIsNone(dev.last_report)

    def test_unexpected_errors_propagate(self):
        dev = self.make()
        with mock.patch.object(hidg.os, "write", side_effect=OSError(errno.EIO, "io")):
            with self.assertRaises(OSError):
                dev.write_report(bytes(8))

    def test_read_output_report_plain(self):
        dev = self.make()
        with mock.patch.object(hidg.os, "read", return_value=b"\x03"):
            self.assertEqual(dev.read_output_report(), b"\x03")
        with mock.patch.object(hidg.os, "read", side_effect=BlockingIOError()):
            self.assertIsNone(dev.read_output_report())


if __name__ == "__main__":
    unittest.main()
```

## tests/test_identity_tool.py

`6968 bytes, 177 lines, sha256 ceb15e090995561ced7c60ac585ee59e501d1a889e11fe85a331abf2853c6d6b`

```python
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

    def test_presented_follows_config(self):
        from hid_bridge.config import parse_config
        cfg = parse_config({"keyboard": {"descriptor": "extended"}, "mouse": {"mode": "absolute"},
                            "gadget": {"max_speed": "high-speed"}})
        presented = tool.presented_from_config(cfg)
        self.assertEqual(presented["interfaces"][0]["report_len"], 65)
        self.assertEqual(presented["interfaces"][0]["bInterval"], 1)
        self.assertEqual((presented["interfaces"][1]["subclass"], presented["interfaces"][1]["protocol"]), (0, 0))
        self.assertEqual(presented["interfaces"][1]["wMaxPacketSize"], 6)
        out = tool.convert(SAMPLE_TOPOLOGY, presented=presented)
        self.assertNotIn("interface 0: reference report descriptor is 65 bytes", out)   # now matches
        self.assertNotIn("interface 1: reference class/subclass/protocol (3, 0, 0)", out)

    def test_no_interface_block_is_flagged(self):
        out = tool.convert(SAMPLE)
        self.assertIn("no interface descriptors found", out)

    def test_output_is_valid_toml(self):
        import tomllib
        data = tomllib.loads(tool.convert(SAMPLE_SERIAL))
        self.assertEqual(data["gadget"]["vendor_id"], 0x1A2C)


if __name__ == "__main__":
    unittest.main()
```

## tests/test_keymap.py

`3256 bytes, 69 lines, sha256 58038515df69ac7b39fada3d210d871a163d43f940e942b19d45a49b5362e513`

```python
import unittest

from hid_bridge import keymap
from hid_bridge.keymap import EVDEV_TO_HID, KEY_ALIASES, KEY_CODES, US_LAYOUT, usage_from_name


class KeymapTests(unittest.TestCase):
    def test_key_codes_unique(self):
        self.assertEqual(len(KEY_CODES), len(set(KEY_CODES.values())))

    def test_letters_digits_and_modifiers(self):
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_A"]], 0x04)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_Z"]], 0x1D)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_1"]], 0x1E)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_0"]], 0x27)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_ENTER"]], 0x28)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_LEFTCTRL"]], 0xE0)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_RIGHTMETA"]], 0xE7)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_F12"]], 0x45)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_F24"]], 0x73)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_KPENTER"]], 0x58)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_102ND"]], 0x64)
        self.assertEqual(EVDEV_TO_HID[KEY_CODES["KEY_YEN"]], 0x89)

    def test_all_usages_in_keyboard_page_range(self):
        for code, usage in EVDEV_TO_HID.items():
            self.assertIn(code, keymap.CODE_NAMES)
            self.assertTrue(0x04 <= usage <= 0xE7, f"{keymap.CODE_NAMES[code]} -> {usage:#x}")

    def test_usages_unique_except_documented_duplicates(self):
        seen = {}
        for code, usage in EVDEV_TO_HID.items():
            seen.setdefault(usage, []).append(keymap.CODE_NAMES[code])
        dupes = {u: names for u, names in seen.items() if len(names) > 1}
        # KEY_COMPOSE and KEY_MENU both mean the Application key.
        self.assertEqual(dupes, {0x65: ["KEY_COMPOSE", "KEY_MENU"]})

    def test_aliases_resolve(self):
        self.assertEqual(usage_from_name("ctrl"), 0xE0)
        self.assertEqual(usage_from_name("Delete"), 0x4C)
        self.assertEqual(usage_from_name("KEY_DELETE"), 0x4C)
        self.assertEqual(usage_from_name("f13"), 0x68)
        self.assertEqual(usage_from_name("f12"), 0x45)
        self.assertEqual(usage_from_name("0x3a"), 0x3A)
        self.assertEqual(usage_from_name("a"), 0x04)
        self.assertEqual(usage_from_name("0"), 0x27)
        with self.assertRaises(KeyError):
            usage_from_name("notakey")
        with self.assertRaises(KeyError):
            usage_from_name("KEY_WLAN")  # not on the keyboard page

    def test_alias_targets_valid(self):
        for name, usage in KEY_ALIASES.items():
            self.assertTrue(0x04 <= usage <= 0xE7, name)

    def test_us_layout_round_trip(self):
        self.assertEqual(US_LAYOUT["a"], (0x04, False))
        self.assertEqual(US_LAYOUT["A"], (0x04, True))
        self.assertEqual(US_LAYOUT["!"], (0x1E, True))
        self.assertEqual(US_LAYOUT[")"], (0x27, True))
        self.assertEqual(US_LAYOUT["\n"], (0x28, False))
        self.assertEqual(US_LAYOUT["?"], (0x38, True))
        printable = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !@#$%^&*()-_=+[]{}\\|;:'\",<.>/?`~\t\n"
        for ch in printable:
            self.assertIn(ch, US_LAYOUT)


if __name__ == "__main__":
    unittest.main()
```

## tests/test_linux_input.py

`1191 bytes, 33 lines, sha256 79db9b5ebe325d0d805ea5fd48f9981770494eff6f27facc8af2aab688d5dd46`

```python
import struct
import unittest

from hid_bridge import linux_input as li


class IoctlTests(unittest.TestCase):
    def test_known_ioctl_numbers(self):
        # Values from <linux/input.h> on a 64-bit kernel.
        self.assertEqual(li.EVIOCGVERSION, 0x80044501)
        self.assertEqual(li.EVIOCGID, 0x80084502)
        self.assertEqual(li.EVIOCGNAME(256), 0x81004506)
        self.assertEqual(li.EVIOCGBIT(0, 4), 0x80044520)
        self.assertEqual(li.EVIOCGBIT(li.EV_KEY, 96), 0x80604521)
        self.assertEqual(li.EVIOCGABS(li.ABS_X), 0x80184540)
        self.assertEqual(li.EVIOCGRAB, 0x40044590)

    def test_input_event_struct_size(self):
        long_size = struct.calcsize("l")
        self.assertEqual(li.INPUT_EVENT.size, 2 * long_size + 8)

    def test_bits_from_buffer(self):
        self.assertEqual(li._bits_from_buffer(bytes([0b00000101, 0b10000000])), {0, 2, 15})
        self.assertEqual(li._bits_from_buffer(b"\x00\x00"), set())

    def test_absinfo_span(self):
        info = li.AbsInfo(0, 0, 32767, 0, 0, 0)
        self.assertEqual(info.span, 32767)
        self.assertEqual(li.AbsInfo(0, 5, 5, 0, 0, 0).span, 1)


if __name__ == "__main__":
    unittest.main()
```

## tests/test_macros.py

`6293 bytes, 155 lines, sha256 7467f144bece4d4c4a0a83a9ae4eec479d46f4c73d04ded9331277af36cf419b`

```python
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
        # modifiers lead the key and follow its release, as fingers do
        self.assertEqual(target.key_events, [{0xE0, 0xE2}, {0xE0, 0xE2, 0x4C}, {0xE0, 0xE2}, set()])
        self.assertEqual(engine.stats()["completed"], 1)
        self.assertEqual(engine.running, 0)

    def test_type_shift_handling(self):
        engine, target = self.make({"t": ["type aB!"]})
        engine.start("t")
        drain(engine, target)
        presses = [ev for ev in target.key_events if any(not (0xE0 <= u <= 0xE7) for u in ev)]
        self.assertEqual(presses, [{0x04}, {0xE1, 0x05}, {0xE1, 0x1E}])
        self.assertIn({0xE1}, target.key_events)   # shift went down in its own report first

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
```

## tests/test_reports.py

`3545 bytes, 86 lines, sha256 c43763c288c911e67f28d27c937e6cb1670149a98e835feb679e2c622793a498`

```python
import unittest

from hid_bridge import linux_input as li
from hid_bridge.reports import (
    absolute_mouse_report,
    keyboard_report,
    relative_mouse_reports,
    scale_abs,
    split_delta,
)


class KeyboardReportTests(unittest.TestCase):
    def test_idle(self):
        self.assertEqual(keyboard_report([]), bytes(8))

    def test_modifiers_and_keys(self):
        report = keyboard_report({0xE0, 0xE2, 0x4C})  # ctrl + alt + delete
        self.assertEqual(report, bytes([0x05, 0x00, 0x4C, 0, 0, 0, 0, 0]))

    def test_six_keys_sorted(self):
        report = keyboard_report([0x09, 0x04, 0x05, 0x06, 0x07, 0x08])
        self.assertEqual(report[2:], bytes([0x04, 0x05, 0x06, 0x07, 0x08, 0x09]))

    def test_rollover_phantom(self):
        report = keyboard_report(range(0x04, 0x0B))  # 7 keys
        self.assertEqual(report, bytes([0x00, 0x00] + [0x01] * 6))

    def test_boot_descriptor_range_drops_high_usages(self):
        report = keyboard_report({0x68, 0x04}, max_array_usage=0x65)  # F13 dropped
        self.assertEqual(report[2:], bytes([0x04, 0, 0, 0, 0, 0]))
        report = keyboard_report({0x68, 0x04}, max_array_usage=0xFF)
        self.assertEqual(report[2:], bytes([0x04, 0x68, 0, 0, 0, 0]))

    def test_modifier_only(self):
        self.assertEqual(keyboard_report({0xE1})[0], 0x02)
        self.assertEqual(keyboard_report({0xE7})[0], 0x80)


class MouseReportTests(unittest.TestCase):
    def test_split_delta(self):
        self.assertEqual(list(split_delta(5)), [5])
        self.assertEqual(list(split_delta(127)), [127])
        self.assertEqual(list(split_delta(128)), [127, 1])
        self.assertEqual(list(split_delta(-300)), [-127, -127, -46])
        self.assertEqual(list(split_delta(0)), [0])

    def test_relative_single(self):
        reports = relative_mouse_reports(0b101, 10, -3, 1, 3)
        self.assertEqual(reports, [bytes([0x05, 10, 0xFD, 1])])

    def test_relative_button_mask(self):
        reports = relative_mouse_reports(0b11111, 0, 0, 0, 3)
        self.assertEqual(reports[0][0], 0b111)
        reports = relative_mouse_reports(0b11111, 0, 0, 0, 5)
        self.assertEqual(reports[0][0], 0b11111)

    def test_relative_large_motion_split(self):
        reports = relative_mouse_reports(0, 300, -130, 0, 3)
        self.assertEqual(len(reports), 3)
        total_x = sum(int.from_bytes(r[1:2], "little", signed=True) for r in reports)
        total_y = sum(int.from_bytes(r[2:3], "little", signed=True) for r in reports)
        self.assertEqual((total_x, total_y), (300, -130))

    def test_absolute(self):
        report = absolute_mouse_report(1, 0x1234, 0x7FFF, -2, 3)
        self.assertEqual(report, bytes([0x01, 0x34, 0x12, 0xFF, 0x7F, 0xFE]))
        self.assertEqual(absolute_mouse_report(0, 99999, -5, 0, 3), bytes([0, 0xFF, 0x7F, 0, 0, 0]))

    def test_scale_abs(self):
        self.assertEqual(scale_abs(0, 0, 32767), 0)
        self.assertEqual(scale_abs(32767, 0, 32767), 32767)
        self.assertEqual(scale_abs(50, 0, 100), 16384)
        self.assertEqual(scale_abs(1919, 0, 1919, 1919), 1919)

    def test_button_bits(self):
        from hid_bridge.reports import BUTTON_BITS
        self.assertEqual(BUTTON_BITS[li.BTN_LEFT], 0)
        self.assertEqual(BUTTON_BITS[li.BTN_RIGHT], 1)
        self.assertEqual(BUTTON_BITS[li.BTN_MIDDLE], 2)
        self.assertEqual(BUTTON_BITS[li.BTN_SIDE], BUTTON_BITS[li.BTN_BACK])
        self.assertEqual(BUTTON_BITS[li.BTN_EXTRA], BUTTON_BITS[li.BTN_FORWARD])


if __name__ == "__main__":
    unittest.main()
```

## tests/test_review_bundle.py

`1786 bytes, 44 lines, sha256 1f5e586d921cc9c001d1686f10ebcc99ffcebe1a33cf467d0db860ab01e0ef4c`

```````python
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
```````

## tools/identity-from-lsusb.py

`11590 bytes, 225 lines, sha256 4f54acf18d72711774579bf579acef6bb1049ac544882ac4c5e297fef48e75d6`

```python
#!/usr/bin/env python3
"""Turn an `lsusb -v` dump of a reference keyboard/mouse into a [gadget] block.

    lsusb -v -d 046d:c534 > reference.txt          # on any Linux machine
    tools/identity-from-lsusb.py reference.txt      # paste output into config.toml
    tools/identity-from-lsusb.py --config /etc/hid-bridge/config.toml reference.txt
                                                    # compare against your actual settings

Copies idVendor, idProduct, bcdDevice, manufacturer/product/serial strings
and the configuration power attributes.  The serial is deliberately
randomised (same length and character class as the original) so the CM5
never shares a serial with the physical unit.  Only the first device in the
dump is used.

It also compares the reference device's descriptor tree (bcdUSB, EP0 size,
interface count, class/subclass/protocol per interface, endpoints, polling
interval, packet size, HID version and report-descriptor length) with what
hid-bridge presents and prints a WARNING comment for every difference, so
you know in advance where a descriptor dump of the clone would not match the
original.
"""
from __future__ import annotations

import random
import re
import sys


def _field(text: str, name: str) -> str | None:
    match = re.search(rf"^\s*{name}\s+(\S+)(?:\s+(.*))?$", text, re.M)
    return match.group(1) if match else None


def _string_field(text: str, name: str) -> str:
    match = re.search(rf"^\s*{name}\s+(\d+)\s*(.*)$", text, re.M)
    if not match or match.group(1) == "0":
        return ""
    return match.group(2).strip()


def _randomise_serial(serial: str, rng: random.Random) -> str:
    out = []
    for ch in serial:
        if ch.isdigit():
            out.append(rng.choice("0123456789"))
        elif ch.isupper() and ch in "ABCDEF":
            out.append(rng.choice("ABCDEF"))
        elif ch.isupper():
            out.append(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ"))
        elif ch.islower():
            out.append(rng.choice("abcdefghijklmnopqrstuvwxyz"))
        else:
            out.append(ch)
    return "".join(out)


# What hid-bridge presents (full-speed, relative mouse, 3 buttons, boot
# keyboard descriptor).  See docs/usb-identity.md.
PRESENTED = {
    "bcdUSB": "2.00 (2.01 with LPM)",
    "bMaxPacketSize0": 64,
    "interfaces": [
        {"class": 3, "subclass": 1, "protocol": 1, "endpoints": 1, "bInterval": 10, "wMaxPacketSize": 8, "bcdHID": "1.01 (1.10 with kernel-patches/0001)", "report_len": 63},
        {"class": 3, "subclass": 1, "protocol": 2, "endpoints": 1, "bInterval": 10, "wMaxPacketSize": 4, "bcdHID": "1.01 (1.10 with kernel-patches/0001)", "report_len": 52},
    ],
}


def presented_from_config(cfg) -> dict:
    """What hid-bridge presents with this configuration (see docs/usb-identity.md)."""
    from hid_bridge.descriptors import keyboard_report_descriptor, mouse_report_descriptor, mouse_report_length
    high_speed = cfg.gadget.max_speed == "high-speed"
    interval = 1 if high_speed else 10
    relative = cfg.mouse.mode == "relative"
    return {
        "bcdUSB": "2.00 (2.01 with LPM on a stock kernel)",
        "bMaxPacketSize0": 64,
        "interfaces": [
            {"class": 3, "subclass": 1, "protocol": 1, "endpoints": 1, "bInterval": interval, "wMaxPacketSize": 8,
             "bcdHID": "1.01 (1.10 with kernel-patches/0001)",
             "report_len": len(keyboard_report_descriptor(cfg.keyboard.descriptor == "extended"))},
            {"class": 3, "subclass": 1 if relative else 0, "protocol": 2 if relative else 0, "endpoints": 1,
             "bInterval": interval, "wMaxPacketSize": mouse_report_length(cfg.mouse.mode),
             "bcdHID": "1.01 (1.10 with kernel-patches/0001)",
             "report_len": len(mouse_report_descriptor(cfg.mouse.mode, cfg.mouse.buttons))},
        ],
    }


def _interfaces(block: str) -> list[dict]:
    """Parse the Interface Descriptor blocks of an lsusb -v dump."""
    found = []
    parts = re.split(r"^\s*Interface Descriptor:\s*$", block, flags=re.M)
    for part in parts[1:]:
        # stop at the next interface/configuration boundary if any slipped through
        iface = {}
        for name in ("bInterfaceNumber", "bAlternateSetting", "bNumEndpoints", "bInterfaceClass",
                     "bInterfaceSubClass", "bInterfaceProtocol"):
            value = _field(part, name)
            iface[name] = int(value) if value and value.isdigit() else None
        hid = re.search(r"bcdHID\s+(\S+)", part)
        iface["bcdHID"] = hid.group(1) if hid else None
        rlen = re.search(r"wDescriptorLength\s+(\d+)", part)
        iface["report_len"] = int(rlen.group(1)) if rlen else None
        endpoints = []
        for ep in re.finditer(r"bEndpointAddress\s+0x([0-9a-fA-F]{2})\s+EP \d+ (IN|OUT).*?wMaxPacketSize\s+0x([0-9a-fA-F]{4}).*?bInterval\s+(\d+)", part, re.S):
            endpoints.append({"dir": ep.group(2), "wMaxPacketSize": int(ep.group(3), 16), "bInterval": int(ep.group(4))})
        iface["endpoints"] = endpoints
        found.append(iface)
    return found


def topology_warnings(block: str, presented: dict | None = None) -> list[str]:
    """Differences between the reference device and what hid-bridge presents."""
    PRESENTED = presented or globals()["PRESENTED"]
    warnings = []
    bcd_usb = _field(block, "bcdUSB")
    if bcd_usb and bcd_usb not in ("2.00", "2.01"):
        warnings.append(f"reference bcdUSB is {bcd_usb}; hid-bridge presents {PRESENTED['bcdUSB']} (kernel-fixed, see docs/usb-identity.md)")
    ep0 = _field(block, "bMaxPacketSize0")
    if ep0 and ep0.isdigit() and int(ep0) != PRESENTED["bMaxPacketSize0"]:
        warnings.append(f"reference bMaxPacketSize0 is {ep0}; hid-bridge presents {PRESENTED['bMaxPacketSize0']} (kernel-fixed)")
    ifaces = [i for i in _interfaces(block) if i.get("bAlternateSetting") in (0, None)]
    if not ifaces:
        warnings.append("no interface descriptors found in the dump (run lsusb -v as root to include them)")
        return warnings
    if len(ifaces) != len(PRESENTED["interfaces"]):
        warnings.append(f"reference has {len(ifaces)} interface(s); hid-bridge presents {len(PRESENTED['interfaces'])} (boot keyboard + boot mouse)")
    for index, (ref, ours) in enumerate(zip(ifaces, PRESENTED["interfaces"])):
        triple = (ref["bInterfaceClass"], ref["bInterfaceSubClass"], ref["bInterfaceProtocol"])
        if triple != (ours["class"], ours["subclass"], ours["protocol"]):
            warnings.append(f"interface {index}: reference class/subclass/protocol {triple}; hid-bridge presents "
                            f"({ours['class']}, {ours['subclass']}, {ours['protocol']})")
        if ref["bNumEndpoints"] is not None and ref["bNumEndpoints"] != ours["endpoints"]:
            warnings.append(f"interface {index}: reference has {ref['bNumEndpoints']} endpoint(s) (an interrupt OUT endpoint?); "
                            f"hid-bridge presents {ours['endpoints']} (LEDs via SET_REPORT on EP0)")
        for ep in ref["endpoints"]:
            if ep["dir"] == "IN":
                if ep["bInterval"] != ours["bInterval"]:
                    warnings.append(f"interface {index}: reference polls every {ep['bInterval']} ms; hid-bridge presents {ours['bInterval']} ms (kernel-fixed at full speed)")
                if ep["wMaxPacketSize"] != ours["wMaxPacketSize"]:
                    warnings.append(f"interface {index}: reference wMaxPacketSize {ep['wMaxPacketSize']}; hid-bridge presents {ours['wMaxPacketSize']} (= report length)")
        if ref["bcdHID"] and ref["bcdHID"] not in ("1.01", "1.10"):
            warnings.append(f"interface {index}: reference bcdHID {ref['bcdHID']}; hid-bridge presents {ours['bcdHID']}")
        elif ref["bcdHID"] == "1.10":
            warnings.append(f"interface {index}: reference bcdHID 1.10; hid-bridge presents 1.01 unless kernel-patches/0001 is installed")
        if ref["report_len"] is not None and ref["report_len"] != ours["report_len"]:
            warnings.append(f"interface {index}: reference report descriptor is {ref['report_len']} bytes; hid-bridge presents {ours['report_len']} "
                            f"(use `usbhid-dump` to compare the bytes; hid-bridge's are spec-exact, not a copy)")
    return warnings


def convert(dump: str, rng: random.Random | None = None, presented: dict | None = None) -> str:
    rng = rng or random.Random()
    # Restrict to the first device block.
    parts = re.split(r"^Bus \d+ Device \d+: ID ", dump, flags=re.M)
    block = parts[1] if len(parts) > 1 else dump

    vid = _field(block, "idVendor")
    pid = _field(block, "idProduct")
    bcd = _field(block, "bcdDevice")
    if not (vid and pid):
        raise SystemExit("could not find idVendor/idProduct in the dump")
    manufacturer = _string_field(block, "iManufacturer")
    product = _string_field(block, "iProduct")
    serial = _string_field(block, "iSerial")
    attrs_match = re.search(r"^\s*bmAttributes\s+0x([0-9a-fA-F]{2})\s*$", block, re.M)
    attrs = int(attrs_match.group(1), 16) if attrs_match else 0xA0
    max_power_match = re.search(r"^\s*(?:MaxPower|bMaxPower)\s+(\d+)mA", block, re.M)
    max_power = int(max_power_match.group(1)) if max_power_match else 100
    bcd_value = int(bcd.replace(".", ""), 16) if bcd else 0x0100

    lines = [
        "[gadget]",
        'name = "hidbridge"',
        f"vendor_id = {vid}",
        f"product_id = {pid}",
        f"device_version = 0x{bcd_value:04x}",
        f'manufacturer = "{manufacturer}"',
        f'product = "{product}"',
        f'serial = "{_randomise_serial(serial, rng)}"' if serial else 'serial = ""',
        'max_speed = "full-speed"',
        f"self_powered = {'true' if attrs & 0x40 else 'false'}",
        f"remote_wakeup = {'true' if attrs & 0x20 else 'false'}",
        f"max_power_ma = {max(1, min(500, max_power))}",
        'udc = ""',
    ]
    notes = []
    if not serial:
        notes.append("# reference has no serial; set all three strings or none (see docs/usb-identity.md)")
    if not (manufacturer or product):
        notes.append("# reference has no strings at all: leave manufacturer/product/serial empty")
    for warning in topology_warnings(block, presented):
        notes.append(f"# WARNING: {warning}")
    if any(n.startswith("# WARNING") for n in notes):
        notes.append("# A descriptor dump of the clone will differ from the original in the points above;")
        notes.append("# pick a reference with matching topology if that matters (docs/remaining-tells.md).")
    return "\n".join(lines + notes) + "\n"


def main(argv: list[str]) -> int:
    args = list(argv[1:])
    presented = None
    if len(args) >= 2 and args[0] == "--config":
        import os
        for candidate in (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "/opt/hid-bridge"):
            if os.path.isdir(os.path.join(candidate, "hid_bridge")) and candidate not in sys.path:
                sys.path.insert(0, candidate)
        from hid_bridge.config import ConfigError, load_config
        try:
            presented = presented_from_config(load_config(args[1]))
        except ConfigError as exc:
            print(f"config error: {exc}", file=sys.stderr)
            return 2
        args = args[2:]
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    with open(args[0], encoding="utf-8", errors="replace") as fh:
        sys.stdout.write(convert(fh.read(), presented=presented))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

## tools/make-review-bundle.py

`8518 bytes, 240 lines, sha256 fde4e92fb2aff4fd6058c2c0bfea5338e60febdd93debde3612c4bcab63ab6d7`

```python
#!/usr/bin/env python3
"""Bundle every tracked file of the project into one Markdown file for review.

    tools/make-review-bundle.py            # (re)writes REVIEW_BUNDLE.md
    tools/make-review-bundle.py --check    # verifies the bundle matches the tree

The bundle is a convenience for code review and portability only; nothing
runs from it.  Each file appears under a heading with its size, line count
and SHA-256, inside a fenced block whose fence is longer than any run of
backticks in the file, so Markdown documents that themselves contain code
fences render correctly.  ``--check`` parses the bundle back into files and
compares every one byte for byte with the working tree, and fails if a
tracked file is missing from the bundle or the bundle contains a file that
is no longer tracked.
"""
from __future__ import annotations

import datetime
import hashlib
import os
import re
import subprocess
import sys

BUNDLE_NAME = "REVIEW_BUNDLE.md"

# Presentation order: reading order for a reviewer.
ORDER = [
    "README.md",
    "docs/GUIDE.md",
    "docs/hardware.md",
    "docs/pikvm.md",
    "docs/usb-identity.md",
    "docs/remaining-tells.md",
    "docs/review-analysis.md",
    "docs/macros.md",
    "docs/troubleshooting.md",
    "config/config.toml",
    "hid_bridge/__init__.py",
    "hid_bridge/__main__.py",
    "hid_bridge/config.py",
    "hid_bridge/descriptors.py",
    "hid_bridge/keymap.py",
    "hid_bridge/reports.py",
    "hid_bridge/linux_input.py",
    "hid_bridge/hidg.py",
    "hid_bridge/gadget.py",
    "hid_bridge/macros.py",
    "hid_bridge/control.py",
    "hid_bridge/bridge.py",
    "tests/",
    "tools/",
    "bin/hid-bridge",
    "systemd/",
    "install.sh",
    "uninstall.sh",
    "Makefile",
    ".gitignore",
    "kernel-patches/README.md",
    "kernel-patches/",
]

LANGUAGES = {
    ".py": "python", ".md": "markdown", ".toml": "toml", ".sh": "bash",
    ".service": "ini", ".patch": "diff", ".ps1": "powershell", ".txt": "text",
}


def repo_root() -> str:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def tracked_files(root: str) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
    files = [f for f in out.stdout.decode().split("\0") if f]
    return [f for f in files if f != BUNDLE_NAME and os.path.isfile(os.path.join(root, f))]


def ordered(files: list[str]) -> list[str]:
    remaining = sorted(files)
    result: list[str] = []
    for key in ORDER:
        if key.endswith("/"):
            group = [f for f in remaining if f.startswith(key)]
        else:
            group = [f for f in remaining if f == key]
        for f in group:
            result.append(f)
            remaining.remove(f)
    return result + remaining


def language_for(path: str) -> str:
    base = os.path.basename(path)
    if base == "Makefile":
        return "makefile"
    if base == "hid-bridge" or base.endswith(".sh"):
        return "bash"
    if base == ".gitignore":
        return "text"
    return LANGUAGES.get(os.path.splitext(base)[1], "text")


def anchor_for(path: str) -> str:
    """GitHub-style heading anchor for ``## <path>``."""
    text = path.lower()
    text = re.sub(r"[^a-z0-9 _-]", "", text)
    return text.replace(" ", "-")


def fence_for(text: str) -> str:
    longest = max((len(m.group(0)) for m in re.finditer(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def git_describe(root: str) -> tuple[str, str]:
    def run(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"
    return run("rev-parse", "--short", "HEAD"), run("rev-parse", "--abbrev-ref", "HEAD")


def build(root: str) -> str:
    files = ordered(tracked_files(root))
    commit, branch = git_describe(root)
    total = 0
    sections: list[str] = []
    toc: list[str] = []
    for index, path in enumerate(files, 1):
        with open(os.path.join(root, path), "rb") as fh:
            raw = fh.read()
        total += len(raw)
        text = raw.decode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        trailing = "" if text.endswith("\n") or not text else " (no trailing newline)"
        fence = fence_for(text)
        body = text if (text.endswith("\n") or not text) else text + "\n"
        toc.append(f"{index}. [{path}](#{anchor_for(path)})")
        sections.append(
            f"## {path}\n\n"
            f"`{len(raw)} bytes, {lines} lines, sha256 {digest}`{trailing}\n\n"
            f"{fence}{language_for(path)}\n{body}{fence}\n"
        )
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        "# hid-bridge: review bundle\n\n"
        "Every tracked file of the project in one document, for code review and\n"
        "portability only.  Nothing runs from this file; install from the\n"
        "repository.  Regenerate with `tools/make-review-bundle.py` (or `make\n"
        "bundle`) and verify with `tools/make-review-bundle.py --check`.\n\n"
        f"* Generated: {now}\n"
        f"* Base commit: `{commit}` on `{branch}` (built from the working tree, so the\n"
        "  content may be ahead of that commit; `--check` compares against the tree)\n"
        f"* Files: {len(files)} ({total:,} bytes)\n\n"
        "## Contents\n\n" + "\n".join(toc) + "\n\n"
    )
    return header + "\n".join(sections)


SECTION_RE = re.compile(
    r"^## (?P<path>\S+)\n\n`(?P<bytes>\d+) bytes, (?P<lines>\d+) lines, sha256 (?P<sha>[0-9a-f]{64})`"
    r"(?P<trailing> \(no trailing newline\))?\n\n(?P<fence>`{3,})(?P<lang>[a-z]*)\n",
    re.M,
)


def parse(bundle: str) -> dict[str, bytes]:
    """Recover {path: content} from a bundle; raises ValueError on malformed sections."""
    files: dict[str, bytes] = {}
    pos = 0
    while True:
        match = SECTION_RE.search(bundle, pos)
        if not match:
            break
        fence = match.group("fence")
        start = match.end()
        end = bundle.find("\n" + fence + "\n", start - 1)
        if end < 0:
            raise ValueError(f"unterminated section for {match.group('path')}")
        body = bundle[start:end + 1]
        if match.group("trailing"):
            body = body[:-1]
        content = body.encode("utf-8")
        if hashlib.sha256(content).hexdigest() != match.group("sha"):
            raise ValueError(f"checksum mismatch inside the bundle for {match.group('path')}")
        files[match.group("path")] = content
        pos = end + len(fence) + 2
    return files


def check(root: str) -> int:
    bundle_path = os.path.join(root, BUNDLE_NAME)
    try:
        with open(bundle_path, encoding="utf-8") as fh:
            bundled = parse(fh.read())
    except FileNotFoundError:
        print(f"{BUNDLE_NAME} does not exist; run tools/make-review-bundle.py", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"{BUNDLE_NAME} is malformed: {exc}", file=sys.stderr)
        return 1
    tracked = set(tracked_files(root))
    problems = []
    for path in sorted(tracked - set(bundled)):
        problems.append(f"missing from bundle: {path}")
    for path in sorted(set(bundled) - tracked):
        problems.append(f"in bundle but not tracked: {path}")
    for path in sorted(tracked & set(bundled)):
        with open(os.path.join(root, path), "rb") as fh:
            if fh.read() != bundled[path]:
                problems.append(f"differs from working tree: {path}")
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"{BUNDLE_NAME} is stale: regenerate with tools/make-review-bundle.py", file=sys.stderr)
        return 1
    print(f"{BUNDLE_NAME}: {len(bundled)} files, all identical to the working tree")
    return 0


def main(argv: list[str]) -> int:
    root = repo_root()
    if argv[1:] == ["--check"]:
        return check(root)
    if argv[1:]:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    bundle = build(root)
    with open(os.path.join(root, BUNDLE_NAME), "w", encoding="utf-8") as fh:
        fh.write(bundle)
    print(f"wrote {BUNDLE_NAME} ({len(bundle.encode()):,} bytes)")
    return check(root)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

## tools/verify-gadget.sh

`2504 bytes, 45 lines, sha256 f7de3ccf43e2038d0ba2181b8f417576f84b9c14d7e68036f75f6fe984214f43`

```bash
#!/bin/sh
# Dump everything the CM5 knows about its own gadget: configfs values, UDC
# state/speed and the hidg device nodes.  Run on the CM5 while it is plugged
# into the target.  Pair it with the host-side checks in docs/usb-identity.md.
G=${1:-/sys/kernel/config/usb_gadget/hidbridge}
echo "== gadget: $G"
[ -d "$G" ] || { echo "gadget not created (systemctl status hid-gadget)"; exit 1; }
for a in idVendor idProduct bcdDevice bcdUSB bDeviceClass bDeviceSubClass bDeviceProtocol bMaxPacketSize0 max_speed UDC; do
    printf '  %-18s %s\n' "$a" "$(cat "$G/$a" 2>/dev/null || echo n/a)"
done
echo "== strings"
for a in manufacturer product serialnumber; do
    printf '  %-18s %s\n' "$a" "$(cat "$G/strings/0x409/$a" 2>/dev/null || echo '(unset)')"
done
echo "== configuration c.1"
for a in bmAttributes MaxPower; do
    printf '  %-18s %s\n' "$a" "$(cat "$G/configs/c.1/$a" 2>/dev/null)"
done
echo "  interfaces (link order = interface number):"
ls -1 "$G/configs/c.1" | grep -v '^strings$' | grep -v '^bmAttributes$' | grep -v '^MaxPower$' | sed 's/^/    /'
for f in "$G"/functions/*; do
    echo "== function $(basename "$f")"
    for a in protocol subclass report_length no_out_endpoint strict_report_types wakeup_on_write interval dev; do
        printf '  %-18s %s\n' "$a" "$(cat "$f/$a" 2>/dev/null || echo n/a)"
    done
    printf '  %-18s %s\n' "report_desc" "$(xxd -p "$f/report_desc" 2>/dev/null | tr -d '\n' || od -An -tx1 "$f/report_desc" | tr -d ' \n')"
done
UDC=$(cat "$G/UDC" 2>/dev/null)
if [ -n "$UDC" ]; then
    echo "== UDC $UDC"
    for a in state current_speed maximum_speed is_a_peripheral function; do
        printf '  %-18s %s\n' "$a" "$(cat "/sys/class/udc/$UDC/$a" 2>/dev/null || echo n/a)"
    done
    printf '  %-18s %s\n' "lpm (debugfs)" "$(grep -E '^\s*lpm\s*[:=]' /sys/kernel/debug/usb/$UDC/params 2>/dev/null | awk '{print $NF}' || echo n/a)"
    echo "  (state should be 'configured' and current_speed 'full-speed' while the target is on;"
    printf '  %-18s %s\n' "suspended" "$(cat "/sys/class/udc/$UDC/gadget/suspended" 2>/dev/null || echo n/a)"
    echo "   lpm 1 means bcdUSB 2.01 plus a BOS descriptor on a stock kernel; with kernel-patches/0002"
    echo "   at full speed the wire is always 2.00 without BOS; suspended 1 = the host suspended the bus)"
else
    echo "== UDC: not bound"
fi
echo "== hidg devices"
ls -l /dev/hidg* 2>/dev/null || echo "  none"
echo "== bridge"
systemctl is-active hid-bridge 2>/dev/null | sed 's/^/  hid-bridge.service: /'
```

## tools/windows/Get-HidBridgeDevices.ps1

`2094 bytes, 47 lines, sha256 8f7567d60121605dc041930e6b9af557e9a9d9b131a678fd92b8b5d8a1569bf3`

```powershell
<#
.SYNOPSIS
  Show how Windows sees the CM5 hid-bridge (run on the target PC, no admin needed).

.DESCRIPTION
  Lists the USB device and its two HID children with hardware IDs, driver,
  and status, so you can confirm the PC sees only "USB Input Device",
  "HID Keyboard Device" and "HID-compliant mouse" bound to Microsoft's
  in-box class drivers.

.PARAMETER Vid
  USB vendor ID as 4 hex digits (default 1209, matching config.toml).
.PARAMETER Pid
  USB product ID as 4 hex digits (default 0001).
#>
param(
    [string]$Vid = "1209",
    [string]$Pid = "0001"
)

$pattern = "VID_$Vid&PID_$Pid"
$devices = Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match $pattern }
if (-not $devices) {
    Write-Host "No present device with $pattern. Is the CM5 plugged in and hid-gadget active?" -ForegroundColor Yellow
    Write-Host "All present USB/HID devices:"
    Get-PnpDevice -PresentOnly -Class USB,HIDClass,Keyboard,Mouse | Sort-Object Class | Format-Table Class, FriendlyName, InstanceId -AutoSize
    exit 1
}

foreach ($d in $devices | Sort-Object InstanceId) {
    Write-Host ""
    Write-Host ("[{0}] {1}" -f $d.Class, $d.FriendlyName) -ForegroundColor Cyan
    Write-Host ("  InstanceId : {0}" -f $d.InstanceId)
    Write-Host ("  Status     : {0}" -f $d.Status)
    $props = Get-PnpDeviceProperty -InstanceId $d.InstanceId -KeyName `
        'DEVPKEY_Device_HardwareIds', 'DEVPKEY_Device_CompatibleIds', 'DEVPKEY_Device_Service', `
        'DEVPKEY_Device_DriverProvider', 'DEVPKEY_Device_BusReportedDeviceDesc' -ErrorAction SilentlyContinue
    foreach ($p in $props) {
        $value = if ($p.Data -is [array]) { $p.Data -join ", " } else { $p.Data }
        Write-Host ("  {0,-30}: {1}" -f ($p.KeyName -replace 'DEVPKEY_Device_', ''), $value)
    }
}

Write-Host ""
Write-Host "Expected: one 'USB Input Device' per interface (Service HidUsb, provider Microsoft)," 
Write-Host "          one 'HID Keyboard Device' (kbdhid) and one 'HID-compliant mouse' (mouhid)."
Write-Host "For raw descriptors use Microsoft's USBView (Windows SDK) or Thesycon USB Descriptor Dumper."
```

## bin/hid-bridge

`185 bytes, 4 lines, sha256 c83d7d1c9b8cf197917d06299ec7dc1d33a5535935af2b84dae45346cace2b19`

```bash
#!/bin/sh
# Thin launcher for the hid_bridge Python package.
export PYTHONPATH="${HID_BRIDGE_HOME:-/opt/hid-bridge}${PYTHONPATH:+:$PYTHONPATH}"
exec /usr/bin/python3 -m hid_bridge "$@"
```

## systemd/hid-bridge.service

`787 bytes, 29 lines, sha256 2d6668cb495be80048eebfcd309806174ab68ce139e616c486908c07add25898`

```ini
[Unit]
Description=hid-bridge: forward PiKVM and macro-pad input to the USB HID gadget
Documentation=file:///opt/hid-bridge/README.md
After=hid-gadget.service
Requires=hid-gadget.service
ConditionPathExists=/etc/hid-bridge/config.toml

[Service]
Type=simple
Environment=PYTHONPATH=/opt/hid-bridge
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 -m hid_bridge run
Restart=always
RestartSec=1
RuntimeDirectory=hid-bridge
RuntimeDirectoryPreserve=yes
# Latency matters: keep the daemon responsive under load.
Nice=-10
IOSchedulingClass=best-effort
IOSchedulingPriority=0
# Hardening that still allows evdev, hidg and configfs access.
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/run/hid-bridge /dev
ProtectHome=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

## systemd/hid-gadget.service

`691 bytes, 22 lines, sha256 a10c5fd0ecb05dfef54d2fb34660fb2a3434e475ffb078e9d9529cbb4c0a8a0a`

```ini
[Unit]
Description=USB HID gadget (keyboard + mouse) for hid-bridge
Documentation=file:///opt/hid-bridge/README.md
After=sys-kernel-config.mount systemd-modules-load.service systemd-udevd.service
Requires=sys-kernel-config.mount
Before=hid-bridge.service
ConditionPathExists=/etc/hid-bridge/config.toml

[Service]
Type=oneshot
RemainAfterExit=yes
Environment=PYTHONPATH=/opt/hid-bridge
Environment=PYTHONUNBUFFERED=1
ExecStartPre=-/sbin/modprobe dwc2
ExecStartPre=-/sbin/modprobe libcomposite
ExecStart=/usr/bin/python3 -m hid_bridge gadget up
ExecStop=/usr/bin/python3 -m hid_bridge gadget down
RuntimeDirectory=hid-bridge
RuntimeDirectoryPreserve=yes

[Install]
WantedBy=multi-user.target
```

## install.sh

`3569 bytes, 83 lines, sha256 25a916f712c458c4b3f4f8d8439028ab3726d3bbb43e17d536dafacf297bf9c7`

```bash
#!/bin/sh
# Install hid-bridge on a Raspberry Pi CM5 running Raspberry Pi OS (Bookworm or newer).
# Usage: sudo ./install.sh          (idempotent; re-run after pulling updates)
set -eu

PREFIX=/opt/hid-bridge
CONFIG_DIR=/etc/hid-bridge
SRC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ "$(id -u)" -ne 0 ]; then
    echo "run as root: sudo $0" >&2
    exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    echo "python3 >= 3.11 is required (Raspberry Pi OS Bookworm ships 3.11)" >&2
    exit 1
fi

echo "==> installing package to $PREFIX"
mkdir -p "$PREFIX"
rm -rf "$PREFIX/hid_bridge"
cp -r "$SRC_DIR/hid_bridge" "$PREFIX/hid_bridge"
find "$PREFIX/hid_bridge" -name '__pycache__' -type d -prune -exec rm -rf {} +
cp "$SRC_DIR/README.md" "$PREFIX/README.md"
rm -rf "$PREFIX/docs"; cp -r "$SRC_DIR/docs" "$PREFIX/docs"
rm -rf "$PREFIX/tools"; cp -r "$SRC_DIR/tools" "$PREFIX/tools"
rm -rf "$PREFIX/kernel-patches"; cp -r "$SRC_DIR/kernel-patches" "$PREFIX/kernel-patches"
install -m 0755 "$SRC_DIR/bin/hid-bridge" /usr/local/bin/hid-bridge

echo "==> configuration"
mkdir -p "$CONFIG_DIR"
if [ -f "$CONFIG_DIR/config.toml" ]; then
    install -m 0644 "$SRC_DIR/config/config.toml" "$CONFIG_DIR/config.toml.dist"
    echo "    kept existing $CONFIG_DIR/config.toml (new defaults in config.toml.dist)"
else
    install -m 0644 "$SRC_DIR/config/config.toml" "$CONFIG_DIR/config.toml"
    # Give this unit a stable, unique serial like a real keyboard would have.
    SERIAL=$(tr -dc 'A-F0-9' </dev/urandom | head -c 12)
    sed -i "s/^serial = \"\"/serial = \"$SERIAL\"/" "$CONFIG_DIR/config.toml"
    echo "    wrote $CONFIG_DIR/config.toml (serial $SERIAL)"
fi

echo "==> kernel modules"
printf 'dwc2\nlibcomposite\n' > /etc/modules-load.d/hid-bridge.conf

BOOT_CONFIG=""
for candidate in /boot/firmware/config.txt /boot/config.txt; do
    if [ -f "$candidate" ]; then BOOT_CONFIG=$candidate; break; fi
done
if [ -n "$BOOT_CONFIG" ]; then
    if grep -Eq '^[[:space:]]*dtoverlay=dwc2' "$BOOT_CONFIG"; then
        if ! grep -Eq '^[[:space:]]*dtoverlay=dwc2.*dr_mode=peripheral' "$BOOT_CONFIG"; then
            echo "    WARNING: $BOOT_CONFIG has a dtoverlay=dwc2 line without dr_mode=peripheral; edit it by hand"
        else
            echo "    $BOOT_CONFIG already has dtoverlay=dwc2,dr_mode=peripheral"
        fi
    else
        cp "$BOOT_CONFIG" "$BOOT_CONFIG.hid-bridge.bak"
        printf '\n# hid-bridge: USB device (gadget) mode on the CM5 USB 2.0 OTG port\n[all]\ndtoverlay=dwc2,dr_mode=peripheral\n' >> "$BOOT_CONFIG"
        echo "    added dtoverlay=dwc2,dr_mode=peripheral to $BOOT_CONFIG (backup: $BOOT_CONFIG.hid-bridge.bak)"
        NEED_REBOOT=1
    fi
else
    echo "    WARNING: no config.txt found; add 'dtoverlay=dwc2,dr_mode=peripheral' to your boot config manually"
fi

echo "==> systemd units"
install -m 0644 "$SRC_DIR/systemd/hid-gadget.service" /etc/systemd/system/hid-gadget.service
install -m 0644 "$SRC_DIR/systemd/hid-bridge.service" /etc/systemd/system/hid-bridge.service
systemctl daemon-reload
systemctl enable hid-gadget.service hid-bridge.service >/dev/null

echo "==> validating configuration"
HID_BRIDGE_CONFIG="$CONFIG_DIR/config.toml" /usr/local/bin/hid-bridge check || true

echo
if [ "${NEED_REBOOT:-0}" = 1 ]; then
    echo "Reboot to activate USB device mode:  sudo reboot"
else
    echo "Start now with:  sudo systemctl start hid-gadget hid-bridge"
fi
echo "Then check:      hid-bridge gadget status ; hid-bridge ctl status ; journalctl -u hid-bridge -f"
```

## uninstall.sh

`793 bytes, 17 lines, sha256 11ab6d8a9764fddc6b5ab26251751e0b0840f89ef83c57296281cdd4513cbb91`

```bash
#!/bin/sh
# Remove hid-bridge (keeps /etc/hid-bridge and the dwc2 overlay line unless --purge).
set -eu
if [ "$(id -u)" -ne 0 ]; then echo "run as root" >&2; exit 1; fi
systemctl disable --now hid-bridge.service hid-gadget.service 2>/dev/null || true
rm -f /etc/systemd/system/hid-bridge.service /etc/systemd/system/hid-gadget.service
systemctl daemon-reload
rm -f /usr/local/bin/hid-bridge /etc/modules-load.d/hid-bridge.conf
rm -rf /opt/hid-bridge
if [ "${1:-}" = "--purge" ]; then
    rm -rf /etc/hid-bridge
    for f in /boot/firmware/config.txt /boot/config.txt; do
        [ -f "$f" ] && sed -i '/^# hid-bridge: USB device (gadget) mode/d;/^dtoverlay=dwc2,dr_mode=peripheral$/d' "$f"
    done
    echo "purged configuration; reboot to leave USB device mode"
fi
echo "hid-bridge removed"
```

## Makefile

`411 bytes, 21 lines, sha256 794473177ab367186155fc86684e1f1730b01dcea0d7207333cee6ee48cd34fe`

```makefile
PYTHON ?= python3

.PHONY: test check install uninstall lint bundle

test:
	$(PYTHON) -m unittest discover -s tests -v

check:
	HID_BRIDGE_CONFIG=config/config.toml $(PYTHON) -m hid_bridge check

lint:
	$(PYTHON) -m pyflakes hid_bridge tests 2>/dev/null || $(PYTHON) -m compileall -q hid_bridge tests

bundle:
	$(PYTHON) tools/make-review-bundle.py

install:
	sudo ./install.sh

uninstall:
	sudo ./uninstall.sh
```

## .gitignore

`61 bytes, 6 lines, sha256 c50d1a44fde942dbef409a511f66ab9e5c6ea05841b9068f5528e8766bbf8705`

```text
__pycache__/
*.pyc
*.egg-info/
.pytest_cache/
/build/
/dist/
```

## kernel-patches/README.md

`5159 bytes, 73 lines, sha256 c94182328300710f0df71a8fbe6788f9b625f5bb2f6a314e44c7ec2a15e644ea`

````markdown
# Optional kernel patches: remove the last Linux-gadget tells

Everything `hid-bridge` can pin from user space is pinned.  The details below
are decided inside the kernel and remain visible to a descriptor dumper, a
USB analyser or a host issuing deliberate control requests (never to
Windows or UEFI, which do not look at them).  The five patches remove them.

| Tell | Stock rpi-6.12.y | With these patches |
|---|---|---|
| HID descriptor `bcdHID` | 1.01 (obsolete; a Linux `usb_f_hid` signature) | 1.10, like real keyboards (0001) |
| Interface string | iInterface points at "HID Interface", a string only the Linux gadget stack emits | iInterface 0, like real keyboards (0001) |
| `GET_IDLE` default | 1 (4 ms) although nothing is ever re-sent | 0 (report on change), consistent (0001) |
| Zero-length packet after every report | each full-size report is followed by a ZLP on the next IN token; no real HID device does that and it halves the report rate | reports queued without ZLP termination (0001) |
| At full speed: `DEVICE_QUALIFIER` / `OTHER_SPEED_CONFIGURATION` | answered (device claims high-speed capability it never used) | STALLed, like every full-speed-only keyboard (0002) |
| At full speed: `bcdUSB` / BOS / LPM when the dwc2 core has LPM enabled | 2.01 + BOS with an LPM capability, and the core ACKs LPM tokens | 2.00, no BOS, LPM left off in the core (0002) |
| `GET_REPORT` for Output/Feature or an undeclared report ID, `SET_REPORT` for Input/Feature or to an interface without an Output report | answered / accepted (an undeclared report ID even waits 2.5 s) | STALLed via the `strict_report_types` attribute (0003), which `hid-bridge gadget up` enables |
| Remote wakeup | bit advertised, key press never wakes a suspended host (dwc2 has no `.wakeup`) | dwc2 `.wakeup` operation plus an f_hid `wakeup_on_write` attribute that `hid-bridge gadget up` enables (0004) |
| `GET_STATUS(Device)` before `SET_CONFIGURATION` | reports Self Powered | reports bus-powered, then follows the configuration (0005) |
| `SET_FEATURE(DEVICE_REMOTE_WAKEUP)` when the configuration has no wakeup bit | ACKed and reflected in `GET_STATUS`, and left enabled across a bus reset | STALLed; both flags cleared on bus reset as USB 2.0 §9.1.1.6 requires (0005) |
| `SET_FEATURE(TEST_MODE)` at full speed | entered | STALLed: test modes are for high-speed capable functions (0005) |
| `GET_STATUS(Interface)` | zero for any wIndex, configured or not | zero for an existing interface of the active configuration, STALL otherwise (0005) |

The patches are generated from and verified against the `rpi-6.12.y` branch of
https://github.com/raspberrypi/linux.  They are small, affect only gadget
mode.  Only 0002 (and the test-mode check in 0005) is specific to full
speed; 0001, 0003, 0004 and the rest of 0005 apply at any speed.  They form
one series and must be applied in order: 0005 relies on 0004's
`wakeup_capable`, otherwise libcomposite strips the remote-wakeup bit from
the configuration descriptor.  **0004 and 0005 have not been exercised on
CM5 hardware yet**; `docs/remaining-tells.md` §3 has the remote-wakeup test
procedure.

## Building on the CM5 (about 60–90 minutes)

```sh
sudo apt install -y git bc bison flex libssl-dev make libc6-dev libncurses5-dev
git clone --depth=1 --branch rpi-6.12.y https://github.com/raspberrypi/linux
cd linux
git apply /opt/hid-bridge/kernel-patches/*.patch     # or ../Pi-CM5-Project/kernel-patches/
KERNEL=kernel_2712
make bcm2712_defconfig
make -j"$(nproc)" Image.gz modules dtbs
sudo make -j"$(nproc)" modules_install
sudo cp /boot/firmware/$KERNEL.img /boot/firmware/$KERNEL-stock.img
sudo cp arch/arm64/boot/Image.gz /boot/firmware/$KERNEL.img
sudo cp arch/arm64/boot/dts/broadcom/*.dtb /boot/firmware/
sudo cp arch/arm64/boot/dts/overlays/*.dtb* /boot/firmware/overlays/
sudo reboot
```

Check with `uname -r` (custom version suffix), `hid-bridge check`
(`kernel-patches/ present: yes`) and `tools/verify-gadget.sh`.  If the
branch has moved and a patch no longer applies, the hunks are a few lines
each; the intent is documented in each patch header.

Keep the patched kernel from being replaced: `sudo apt-mark hold
linux-image-rpi-2712 linux-image-rpi-v8` (package names vary by release), or
rebuild after each kernel update.  Cross-compiling from a PC follows the
official Raspberry Pi kernel documentation with the same `git apply` step.

## What the patches do not touch

* `bMaxPacketSize0 = 64` and `bcdUSB 2.00`: physically true for the dwc2
  controller; many real full-speed keyboards report the same.  A USB 1.1
  clone (bcdUSB 1.10, EP0 8) would need dwc2 to use an 8-byte EP0 at full
  speed and libcomposite to honour the configfs bcdUSB; feasible (the
  low-speed path already uses 8) but not written; `docs/review-analysis.md`
  item 3 sketches it as a possible 0006.
* `bInterval` fixed at 10 ms (full speed): typical for keyboards and cheap
  mice; adding a configfs attribute is a larger change than is warranted.
* `GET_IDLE` power-up default: HID 1.11 recommends 500 ms for keyboards,
  which would require the function to re-send reports periodically; 0
  matches what it does.
````

## kernel-patches/0001-usb-gadget-f_hid-hid-1.10-idle-0-no-interface-string-no-zlp.patch

`4471 bytes, 110 lines, sha256 a049de728a05c697372cebc7273dd1d211f5c385697c8b5b31fb90ee19588eee`

```diff
From: hid-bridge project
Subject: [PATCH 1/5] usb: gadget: f_hid: report HID 1.10, idle rate 0, no interface string, no ZLP after reports

Real HID keyboards report bcdHID 0x0110; the function reported the
obsolete 1.01.  The default idle rate was 1 (4 ms) although the function
never re-sends unchanged reports; 0 ("indefinite", report on change only)
describes the actual behaviour.  The function also attached an interface
string "HID Interface" to every interface, which real keyboards and mice
do not have and which identifies the Linux gadget stack by name; leave
iInterface at 0.

f_hidg_write queued every report with req->zero = 1.  Reports are at most
wMaxPacketSize, so a full-size report (the normal case: the endpoint size
is the report length) was followed by a zero-length packet on the next IN
token.  No real HID device does that, and the ZLP occupied the next poll
slot, so the function could deliver at most one report every two polls.
Queue reports without ZLP termination.

---
diff --git a/drivers/usb/gadget/function/f_hid.c b/drivers/usb/gadget/function/f_hid.c
index 2f4a5d2..b26ab8c 100644
--- a/drivers/usb/gadget/function/f_hid.c
+++ b/drivers/usb/gadget/function/f_hid.c
@@ -142,7 +142,7 @@ static struct usb_interface_descriptor hidg_interface_desc = {
 static struct hid_descriptor hidg_desc = {
 	.bLength			= sizeof hidg_desc,
 	.bDescriptorType		= HID_DT_HID,
-	.bcdHID				= cpu_to_le16(0x0101),
+	.bcdHID				= cpu_to_le16(0x0110),
 	.bCountryCode			= 0x00,
 	.bNumDescriptors		= 0x1,
 	/*.rpt_desc.bDescriptorType	= DYNAMIC */
@@ -296,22 +296,6 @@ static struct usb_descriptor_header *hidg_fs_descriptors_ssreport[] = {
 /*-------------------------------------------------------------------------*/
 /*                                 Strings                                 */
 
-#define CT_FUNC_HID_IDX	0
-
-static struct usb_string ct_func_string_defs[] = {
-	[CT_FUNC_HID_IDX].s	= "HID Interface",
-	{},			/* end of list */
-};
-
-static struct usb_gadget_strings ct_func_string_table = {
-	.language	= 0x0409,	/* en-US */
-	.strings	= ct_func_string_defs,
-};
-
-static struct usb_gadget_strings *ct_func_strings[] = {
-	&ct_func_string_table,
-	NULL,
-};
 
 /*-------------------------------------------------------------------------*/
 /*                              Char Device                                */
@@ -526,7 +510,14 @@ try_again:
 	}
 
 	req->status   = 0;
-	req->zero     = 1;
+	/*
+	 * A HID report never exceeds wMaxPacketSize, so one packet is the
+	 * whole transfer; never append a zero-length packet.  With zero = 1
+	 * every full-size report was followed by a ZLP, which no real HID
+	 * device sends and which occupied the next poll slot, halving the
+	 * achievable report rate.
+	 */
+	req->zero     = 0;
 	req->length   = count;
 	req->complete = f_hidg_req_complete;
 	req->context  = hidg;
@@ -1163,7 +1154,6 @@ static int hidg_bind(struct usb_configuration *c, struct usb_function *f)
 {
 	struct usb_ep		*ep;
 	struct f_hidg		*hidg = func_to_hidg(f);
-	struct usb_string	*us;
 	int			status;
 
 	hidg->get_req = usb_ep_alloc_request(c->cdev->gadget->ep0, GFP_ATOMIC);
@@ -1175,12 +1165,11 @@ static int hidg_bind(struct usb_configuration *c, struct usb_function *f)
 	hidg->get_req->context = hidg;
 	hidg->get_report_returned = true;
 
-	/* maybe allocate device-global string IDs, and patch descriptors */
-	us = usb_gstrings_attach(c->cdev, ct_func_strings,
-				 ARRAY_SIZE(ct_func_string_defs));
-	if (IS_ERR(us))
-		return PTR_ERR(us);
-	hidg_interface_desc.iInterface = us[CT_FUNC_HID_IDX].id;
+	/*
+	 * Real HID keyboards and mice carry no interface string, and the
+	 * former "HID Interface" string identified the Linux gadget stack.
+	 */
+	hidg_interface_desc.iInterface = 0;
 
 	/* allocate instance-specific interface IDs, and patch descriptors */
 	status = usb_interface_id(c, f);
@@ -1211,7 +1200,11 @@ static int hidg_bind(struct usb_configuration *c, struct usb_function *f)
 	hidg_interface_desc.bInterfaceProtocol = hidg->bInterfaceProtocol;
 	hidg_interface_desc.bNumEndpoints = hidg->use_out_ep ? 2 : 1;
 	hidg->protocol = HID_REPORT_PROTOCOL;
-	hidg->idle = 1;
+	/*
+	 * Idle rate 0 = report only on change, which is what this function
+	 * actually does (it never re-sends unchanged reports).
+	 */
+	hidg->idle = 0;
 	hidg_ss_in_ep_desc.wMaxPacketSize = cpu_to_le16(hidg->report_length);
 	hidg_ss_in_comp_desc.wBytesPerInterval =
 				cpu_to_le16(hidg->report_length);
```

## kernel-patches/0002-usb-gadget-composite-full-speed-only-when-limited-to-full-speed.patch

`3637 bytes, 88 lines, sha256 8c7079362a9f866a2916cd1320bf4f3e63129adeebed8fba742950dc21f3aabe`

```diff
From: hid-bridge project
Subject: [PATCH 2/5] usb: gadget: composite, dwc2: behave as a full-speed-only device when limited to full speed

When the composite driver's max_speed is full speed (configfs max_speed =
"full-speed") the host sees a device that never chirps.  Present it as the
plain full-speed device it appears to be: STALL DEVICE_QUALIFIER and
OTHER_SPEED_CONFIGURATION (USB 2.0 section 9.6.2 for full-speed-only
devices), keep bcdUSB at 0x0200 and offer no BOS descriptor even when the
controller hardware is LPM capable, and have dwc2 leave LPM acceptance off
in that case so the wire matches the descriptors.  The controller's own
max_speed stays high (dwc2 does not lower it), which is why the driver's
limit has to be consulted.  Ordinary keyboards do not advertise LPM.

---
diff --git a/drivers/usb/dwc2/gadget.c b/drivers/usb/dwc2/gadget.c
index 324630a..71b8dac 100644
--- a/drivers/usb/dwc2/gadget.c
+++ b/drivers/usb/dwc2/gadget.c
@@ -5293,6 +5293,16 @@ void dwc2_gadget_init_lpm(struct dwc2_hsotg *hsotg)
 	if (!hsotg->params.lpm)
 		return;
 
+	/*
+	 * A gadget driver limited to full speed presents a device whose
+	 * descriptors do not advertise LPM (see composite.c); do not let the
+	 * core accept LPM transactions either, so the wire matches them.
+	 */
+	if (hsotg->driver && hsotg->driver->max_speed < USB_SPEED_HIGH) {
+		dwc2_writel(hsotg, 0, GLPMCFG);
+		return;
+	}
+
 	val = GLPMCFG_LPMCAP | GLPMCFG_APPL1RES;
 	val |= hsotg->params.hird_threshold_en ? GLPMCFG_HIRD_THRES_EN : 0;
 	val |= hsotg->params.lpm_clock_gating ? GLPMCFG_ENBLSLPM : 0;
diff --git a/drivers/usb/gadget/composite.c b/drivers/usb/gadget/composite.c
index 81ff697..88e890f 100644
--- a/drivers/usb/gadget/composite.c
+++ b/drivers/usb/gadget/composite.c
@@ -1839,7 +1839,14 @@ composite_setup(struct usb_gadget *gadget, const struct usb_ctrlrequest *ctrl)
 					cdev->desc.bcdUSB = cpu_to_le16(0x0210);
 				}
 			} else {
-				if (gadget->lpm_capable || cdev->use_webusb)
+				/*
+				 * USB 2.0 LPM (L1) only exists for high-speed
+				 * operation; a gadget limited to full speed must
+				 * not advertise it or a BOS descriptor.
+				 */
+				if ((gadget->lpm_capable &&
+				     cdev->driver->max_speed >= USB_SPEED_HIGH) ||
+				    cdev->use_webusb)
 					cdev->desc.bcdUSB = cpu_to_le16(0x0201);
 				else
 					cdev->desc.bcdUSB = cpu_to_le16(0x0200);
@@ -1849,7 +1856,13 @@ composite_setup(struct usb_gadget *gadget, const struct usb_ctrlrequest *ctrl)
 			memcpy(req->buf, &cdev->desc, value);
 			break;
 		case USB_DT_DEVICE_QUALIFIER:
+			/*
+			 * A gadget driver limited to full speed is a
+			 * full-speed-only device as far as the host can tell
+			 * and must reject qualifier requests (USB 2.0 9.6.2).
+			 */
 			if (!gadget_is_dualspeed(gadget) ||
+			    cdev->driver->max_speed < USB_SPEED_HIGH ||
 			    gadget->speed >= USB_SPEED_SUPER)
 				break;
 			device_qual(cdev);
@@ -1858,6 +1871,7 @@ composite_setup(struct usb_gadget *gadget, const struct usb_ctrlrequest *ctrl)
 			break;
 		case USB_DT_OTHER_SPEED_CONFIG:
 			if (!gadget_is_dualspeed(gadget) ||
+			    cdev->driver->max_speed < USB_SPEED_HIGH ||
 			    gadget->speed >= USB_SPEED_SUPER)
 				break;
 			fallthrough;
@@ -1874,7 +1888,9 @@ composite_setup(struct usb_gadget *gadget, const struct usb_ctrlrequest *ctrl)
 			break;
 		case USB_DT_BOS:
 			if (gadget_is_superspeed(gadget) ||
-			    gadget->lpm_capable || cdev->use_webusb) {
+			    (gadget->lpm_capable &&
+			     cdev->driver->max_speed >= USB_SPEED_HIGH) ||
+			    cdev->use_webusb) {
 				value = bos_desc(cdev);
 				value = min(w_length, (u16) value);
 			}
```

## kernel-patches/0003-usb-gadget-f_hid-add-strict_report_types-option.patch

`7020 bytes, 189 lines, sha256 99197b1bc78fefef1ca02020c1dcd2e4e2b0edcea05fcf4d1c51c875ae1192eb`

```diff
From: hid-bridge project
Subject: [PATCH 3/5] usb: gadget: f_hid: add strict_report_types option

The function ignores the report type and report ID in wValue of the
GET_REPORT and SET_REPORT class requests.  A GET_REPORT for a Feature or
Output report is answered with the Input report, a GET_REPORT for a report
ID the descriptor does not declare waits 2.5 s and answers zeros, and a
SET_REPORT of any type (including an Input report, which a host never
legitimately sends, or an Output report to a function whose descriptor has
none) is delivered to user space as if it were the LED report.  Real
devices STALL those requests.

Add a configfs attribute strict_report_types (default 0, previous
behaviour).  When set, GET_REPORT is served only for report type Input,
SET_REPORT is accepted only for report type Output and only when the
report descriptor declares an Output item, and a non-zero report ID is
rejected when the descriptor uses none.  The descriptor is scanned once at
bind.

---
diff --git a/Documentation/ABI/testing/configfs-usb-gadget-hid b/Documentation/ABI/testing/configfs-usb-gadget-hid
index 748705c..fd8727f 100644
--- a/Documentation/ABI/testing/configfs-usb-gadget-hid
+++ b/Documentation/ABI/testing/configfs-usb-gadget-hid
@@ -4,10 +4,20 @@ KernelVersion:	3.19
 Description:
 		The attributes:
 
-		=============	============================================
-		protocol	HID protocol to use
-		report_desc	blob corresponding to HID report descriptors
-				except the data passed through /dev/hidg<N>
-		report_length	HID report length
-		subclass	HID device subclass to use
-		=============	============================================
+		===================	====================================
+		protocol		HID protocol to use
+		report_desc		blob corresponding to HID report
+					descriptors except the data passed
+					through /dev/hidg<N>
+		report_length		HID report length
+		subclass		HID device subclass to use
+		no_out_endpoint		if 1, receive reports via SET_REPORT
+					on the control endpoint instead of an
+					interrupt OUT endpoint
+		strict_report_types	if 1, serve GET_REPORT only for Input
+					reports, accept SET_REPORT only for
+					Output reports declared by the report
+					descriptor, and reject report IDs the
+					descriptor does not use; STALL
+					everything else as a real device does
+		===================	====================================
diff --git a/drivers/usb/gadget/function/f_hid.c b/drivers/usb/gadget/function/f_hid.c
index b26ab8c..6677da8 100644
--- a/drivers/usb/gadget/function/f_hid.c
+++ b/drivers/usb/gadget/function/f_hid.c
@@ -30,6 +30,10 @@
  */
 #define GET_REPORT_TIMEOUT_MS 2500
 
+/* Report type in the high byte of wValue (HID 1.11, 7.2.1 / 7.2.2) */
+#define HID_WIRE_REPORT_TYPE_INPUT	1
+#define HID_WIRE_REPORT_TYPE_OUTPUT	2
+
 static int major, minors;
 
 static const struct class hidg_class = {
@@ -71,6 +75,17 @@ struct f_hidg {
 	 *              will be used to receive reports.
 	 */
 	bool				use_out_ep;
+	/*
+	 * strict_report_types - if true, validate the report type in the
+	 *              wValue of GET_REPORT/SET_REPORT like a real device
+	 *              with only Input and Output reports does: GET_REPORT is
+	 *              only served for Input reports and SET_REPORT is only
+	 *              accepted for Output reports; anything else is STALLed.
+	 */
+	bool				strict_report_types;
+	/* derived from the report descriptor at bind (see hidg_scan_report_desc) */
+	bool				has_output_report;
+	bool				uses_report_ids;
 
 	/* recv report */
 	spinlock_t			read_spinlock;
@@ -865,6 +880,11 @@ static int hidg_setup(struct usb_function *f,
 		  | HID_REQ_GET_REPORT):
 		VDBG(cdev, "get_report | wLength=%d\n", ctrl->wLength);
 
+		if (hidg->strict_report_types &&
+		    ((value >> 8) != HID_WIRE_REPORT_TYPE_INPUT ||
+		     (!hidg->uses_report_ids && (value & 0xff) != 0)))
+			goto stall;
+
 		/*
 		 * Update GET_REPORT ID so that an ioctl can be used to determine what
 		 * GET_REPORT the request was actually for.
@@ -899,6 +919,11 @@ static int hidg_setup(struct usb_function *f,
 		VDBG(cdev, "set_report | wLength=%d\n", ctrl->wLength);
 		if (hidg->use_out_ep)
 			goto stall;
+		if (hidg->strict_report_types &&
+		    ((value >> 8) != HID_WIRE_REPORT_TYPE_OUTPUT ||
+		     !hidg->has_output_report ||
+		     (!hidg->uses_report_ids && (value & 0xff) != 0)))
+			goto stall;
 		req->complete = hidg_ssreport_complete;
 		req->context  = hidg;
 		goto respond;
@@ -1150,6 +1175,42 @@ static const struct file_operations f_hidg_fops = {
 	.llseek		= noop_llseek,
 };
 
+/*
+ * hidg_scan_report_desc - note whether the report descriptor declares any
+ * Output main items and whether it uses Report IDs.  Short items only need
+ * the prefix byte; long items (0xfe) carry their size in the next byte.
+ */
+static void hidg_scan_report_desc(struct f_hidg *hidg)
+{
+	const unsigned char *desc = hidg->report_desc;
+	unsigned int len = hidg->report_desc_length;
+	unsigned int i = 0;
+
+	hidg->has_output_report = false;
+	hidg->uses_report_ids = false;
+	if (!desc)
+		return;
+
+	while (i < len) {
+		unsigned char prefix = desc[i++];
+		unsigned int size = prefix & 0x03;
+
+		if (prefix == 0xfe) {
+			if (i >= len)
+				break;
+			i += desc[i] + 2;
+			continue;
+		}
+		if (size == 3)
+			size = 4;
+		if ((prefix & 0xfc) == 0x90)		/* Main item: Output */
+			hidg->has_output_report = true;
+		else if ((prefix & 0xfc) == 0x84)	/* Global item: Report ID */
+			hidg->uses_report_ids = true;
+		i += size;
+	}
+}
+
 static int hidg_bind(struct usb_configuration *c, struct usb_function *f)
 {
 	struct usb_ep		*ep;
@@ -1366,6 +1427,7 @@ CONFIGFS_ATTR(f_hid_opts_, name)
 F_HID_OPT(subclass, 8, 255);
 F_HID_OPT(protocol, 8, 255);
 F_HID_OPT(no_out_endpoint, 8, 1);
+F_HID_OPT(strict_report_types, 8, 1);
 F_HID_OPT(report_length, 16, 65535);
 
 static ssize_t f_hid_opts_report_desc_show(struct config_item *item, char *page)
@@ -1426,6 +1488,7 @@ static struct configfs_attribute *hid_attrs[] = {
 	&f_hid_opts_attr_subclass,
 	&f_hid_opts_attr_protocol,
 	&f_hid_opts_attr_no_out_endpoint,
+	&f_hid_opts_attr_strict_report_types,
 	&f_hid_opts_attr_report_length,
 	&f_hid_opts_attr_report_desc,
 	&f_hid_opts_attr_dev,
@@ -1571,6 +1634,8 @@ static struct usb_function *hidg_alloc(struct usb_function_instance *fi)
 		}
 	}
 	hidg->use_out_ep = !opts->no_out_endpoint;
+	hidg->strict_report_types = opts->strict_report_types;
+	hidg_scan_report_desc(hidg);
 
 	++opts->refcnt;
 	mutex_unlock(&opts->lock);
diff --git a/drivers/usb/gadget/function/u_hid.h b/drivers/usb/gadget/function/u_hid.h
index 84bb702..0ede046 100644
--- a/drivers/usb/gadget/function/u_hid.h
+++ b/drivers/usb/gadget/function/u_hid.h
@@ -21,6 +21,7 @@ struct f_hid_opts {
 	unsigned char			subclass;
 	unsigned char			protocol;
 	unsigned char			no_out_endpoint;
+	unsigned char			strict_report_types;
 	unsigned short			report_length;
 	unsigned short			report_desc_length;
 	unsigned char			*report_desc;
```

## kernel-patches/0004-usb-dwc2-gadget-remote-wakeup-f_hid-wakeup_on_write.patch

`9309 bytes, 251 lines, sha256 c6630b0f1cf1ebec4611205e34cfba41dd26001388af7cb35cfb2a19591b8ffd`

```diff
From: hid-bridge project
Subject: [PATCH 4/5] usb: dwc2: gadget: implement remote wakeup; f_hid: wakeup_on_write

STATUS: written against rpi-6.12.y and verified to apply, NOT yet tested on
CM5 hardware.  Review the dwc2 hunk before deploying.

dwc2 advertises remote wakeup capability (configfs bmAttributes bit 5) and
records the host's SET_FEATURE(DEVICE_REMOTE_WAKEUP), but has no gadget
.wakeup operation, so no function can ever initiate resume signalling.  Add
one that waits the 5 ms minimum suspend time of USB 2.0 section 7.1.7.7,
then mirrors the device-mode path of the wakeup-detected interrupt handler
with remote wakeup signalling enabled (hibernation exit, partial power
down exit plus an explicit RmtWkUpSig, clock-gating exit, or a plain
DCTL.RmtWkUpSig), and clears RmtWkUpSig after 2-5 ms.  Mark the gadget
wakeup_capable so libcomposite keeps the configuration's wakeup bit.

Give usb_f_hid a wakeup_on_write attribute: when set and the composite
device is suspended, a write to /dev/hidgN requests remote wakeup before
queueing, so a key press on a suspended host wakes it like a real keyboard.
The composite device is only dereferenced once the function is known to
be configured (hidg->req set).

---
diff --git a/Documentation/ABI/testing/configfs-usb-gadget-hid b/Documentation/ABI/testing/configfs-usb-gadget-hid
index fd8727f..8fb6474 100644
--- a/Documentation/ABI/testing/configfs-usb-gadget-hid
+++ b/Documentation/ABI/testing/configfs-usb-gadget-hid
@@ -20,4 +20,9 @@ Description:
 					descriptor, and reject report IDs the
 					descriptor does not use; STALL
 					everything else as a real device does
+		wakeup_on_write		if 1, a write to /dev/hidg<N> while
+					the bus is suspended first requests
+					USB remote wakeup (the UDC must
+					implement it and the host must have
+					enabled it)
 		===================	====================================
diff --git a/drivers/usb/dwc2/gadget.c b/drivers/usb/dwc2/gadget.c
index 71b8dac..e650c7b 100644
--- a/drivers/usb/dwc2/gadget.c
+++ b/drivers/usb/dwc2/gadget.c
@@ -4793,12 +4793,111 @@ static void dwc2_gadget_set_speed(struct usb_gadget *g, enum usb_device_speed sp
 	spin_unlock_irqrestore(&hsotg->lock, flags);
 }
 
+/**
+ * dwc2_hsotg_gadget_wakeup - initiate USB remote wakeup from device mode
+ * @gadget: The usb gadget state
+ *
+ * Called by gadget functions (usb_gadget_wakeup()) when the host has
+ * suspended the bus, enabled DEVICE_REMOTE_WAKEUP and the function has
+ * new data, e.g. a key press.  Mirrors the device-mode half of
+ * dwc2_handle_wakeup_detected_intr() but with remote wakeup signalling
+ * enabled, and clears the RmtWkUpSig bit again after the 1-15 ms the USB
+ * specification allows (section 7.1.7.7).  Must be called from process
+ * context.
+ */
+static int dwc2_hsotg_gadget_wakeup(struct usb_gadget *gadget)
+{
+	struct dwc2_hsotg *hsotg = to_hsotg(gadget);
+	unsigned long flags;
+	bool signalled = false;
+	u32 dctl;
+	int ret = 0;
+
+	/*
+	 * USB 2.0 7.1.7.7: a device may only drive resume after it has been
+	 * in Suspend for at least 5 ms.  The suspend interrupt fires ~3 ms
+	 * into bus idle, so a caller reacting to it immediately would be
+	 * early; waiting here costs nothing when the suspend is old.
+	 */
+	usleep_range(5000, 6000);
+
+	spin_lock_irqsave(&hsotg->lock, flags);
+
+	if (!hsotg->remote_wakeup_allowed) {
+		dev_dbg(hsotg->dev, "%s: remote wakeup not enabled by host\n",
+			__func__);
+		ret = -EINVAL;
+		goto out;
+	}
+
+	if (hsotg->lx_state != DWC2_L2) {
+		/* Not suspended (or in L1, which ep_queue exits itself) */
+		ret = -EINVAL;
+		goto out;
+	}
+
+	if (hsotg->hibernated) {
+		/* Restores the core and drives RmtWkUpSig itself (1-15 ms) */
+		ret = dwc2_gadget_exit_hibernation(hsotg, 1, 0);
+		if (ret)
+			dev_err(hsotg->dev, "exit hibernation failed\n");
+		goto out;
+	}
+
+	if (hsotg->in_ppd) {
+		ret = dwc2_exit_partial_power_down(hsotg, 1, true);
+		if (ret) {
+			dev_err(hsotg->dev, "exit partial_power_down failed\n");
+			goto out;
+		}
+		/*
+		 * The device-mode exit path restores DCTL from the backup and
+		 * never asserts RmtWkUpSig itself; do it after the restore.
+		 */
+		dctl = dwc2_readl(hsotg, DCTL);
+		dctl |= DCTL_RMTWKUPSIG;
+		dwc2_writel(hsotg, dctl, DCTL);
+		call_gadget(hsotg, resume);
+		signalled = true;
+	} else if (hsotg->params.power_down == DWC2_POWER_DOWN_PARAM_NONE &&
+		   hsotg->bus_suspended && !hsotg->params.no_clock_gating) {
+		/* Ungate clocks, sets RmtWkUpSig and returns to L0 */
+		dwc2_gadget_exit_clock_gating(hsotg, 1);
+		signalled = true;
+	} else {
+		dctl = dwc2_readl(hsotg, DCTL);
+		dctl |= DCTL_RMTWKUPSIG;
+		dwc2_writel(hsotg, dctl, DCTL);
+		call_gadget(hsotg, resume);
+		hsotg->lx_state = DWC2_L0;
+		hsotg->bus_suspended = false;
+		signalled = true;
+	}
+
+out:
+	spin_unlock_irqrestore(&hsotg->lock, flags);
+
+	if (signalled) {
+		/* Drive resume signalling for 1-15 ms, then release the bus */
+		usleep_range(2000, 5000);
+		spin_lock_irqsave(&hsotg->lock, flags);
+		dctl = dwc2_readl(hsotg, DCTL);
+		dctl &= ~DCTL_RMTWKUPSIG;
+		dwc2_writel(hsotg, dctl, DCTL);
+		spin_unlock_irqrestore(&hsotg->lock, flags);
+		dev_dbg(hsotg->dev, "%s: remote wakeup signalled\n", __func__);
+	}
+
+	return ret;
+}
+
 static const struct usb_gadget_ops dwc2_hsotg_gadget_ops = {
 	.get_frame	= dwc2_hsotg_gadget_getframe,
 	.set_selfpowered	= dwc2_hsotg_set_selfpowered,
 	.udc_start		= dwc2_hsotg_udc_start,
 	.udc_stop		= dwc2_hsotg_udc_stop,
 	.pullup                 = dwc2_hsotg_pullup,
+	.wakeup			= dwc2_hsotg_gadget_wakeup,
 	.udc_set_speed		= dwc2_gadget_set_speed,
 	.vbus_session		= dwc2_hsotg_vbus_session,
 	.vbus_draw		= dwc2_hsotg_vbus_draw,
@@ -5024,6 +5123,9 @@ int dwc2_gadget_init(struct dwc2_hsotg *hsotg)
 	if (hsotg->params.lpm)
 		hsotg->gadget.lpm_capable = true;
 
+	/* .wakeup is implemented: keep libcomposite's remote-wakeup bit */
+	hsotg->gadget.wakeup_capable = true;
+
 	if (hsotg->dr_mode == USB_DR_MODE_OTG)
 		hsotg->gadget.is_otg = 1;
 	else if (hsotg->dr_mode == USB_DR_MODE_PERIPHERAL)
diff --git a/drivers/usb/gadget/function/f_hid.c b/drivers/usb/gadget/function/f_hid.c
index 6677da8..b50b6db 100644
--- a/drivers/usb/gadget/function/f_hid.c
+++ b/drivers/usb/gadget/function/f_hid.c
@@ -86,6 +86,12 @@ struct f_hidg {
 	/* derived from the report descriptor at bind (see hidg_scan_report_desc) */
 	bool				has_output_report;
 	bool				uses_report_ids;
+	/*
+	 * wakeup_on_write - if true, a write while the bus is suspended first
+	 *              requests USB remote wakeup, as a real keyboard does when
+	 *              a key is pressed while the host sleeps.
+	 */
+	bool				wakeup_on_write;
 
 	/* recv report */
 	spinlock_t			read_spinlock;
@@ -466,6 +472,7 @@ static ssize_t f_hidg_write(struct file *file, const char __user *buffer,
 			    size_t count, loff_t *offp)
 {
 	struct f_hidg *hidg  = file->private_data;
+	struct usb_composite_dev *cdev;
 	struct usb_request *req;
 	unsigned long flags;
 	ssize_t status = -ENOMEM;
@@ -477,6 +484,26 @@ static ssize_t f_hidg_write(struct file *file, const char __user *buffer,
 		return -ESHUTDOWN;
 	}
 
+	/*
+	 * New data while the host has us suspended: ask for remote wakeup
+	 * before queueing, otherwise the request cannot be submitted.  The
+	 * UDC refuses (-EINVAL) when the host did not enable remote wakeup.
+	 * hidg->req being set means the function is bound and configured,
+	 * so func.config->cdev is valid here.
+	 */
+	if (hidg->wakeup_on_write) {
+		cdev = hidg->func.config->cdev;
+		if (cdev->suspended) {
+			spin_unlock_irqrestore(&hidg->write_spinlock, flags);
+			usb_gadget_wakeup(cdev->gadget);
+			spin_lock_irqsave(&hidg->write_spinlock, flags);
+			if (!hidg->req) {
+				spin_unlock_irqrestore(&hidg->write_spinlock, flags);
+				return -ESHUTDOWN;
+			}
+		}
+	}
+
 #define WRITE_COND (!hidg->write_pending)
 try_again:
 	/* write queue */
@@ -1428,6 +1455,7 @@ F_HID_OPT(subclass, 8, 255);
 F_HID_OPT(protocol, 8, 255);
 F_HID_OPT(no_out_endpoint, 8, 1);
 F_HID_OPT(strict_report_types, 8, 1);
+F_HID_OPT(wakeup_on_write, 8, 1);
 F_HID_OPT(report_length, 16, 65535);
 
 static ssize_t f_hid_opts_report_desc_show(struct config_item *item, char *page)
@@ -1489,6 +1517,7 @@ static struct configfs_attribute *hid_attrs[] = {
 	&f_hid_opts_attr_protocol,
 	&f_hid_opts_attr_no_out_endpoint,
 	&f_hid_opts_attr_strict_report_types,
+	&f_hid_opts_attr_wakeup_on_write,
 	&f_hid_opts_attr_report_length,
 	&f_hid_opts_attr_report_desc,
 	&f_hid_opts_attr_dev,
@@ -1635,6 +1664,7 @@ static struct usb_function *hidg_alloc(struct usb_function_instance *fi)
 	}
 	hidg->use_out_ep = !opts->no_out_endpoint;
 	hidg->strict_report_types = opts->strict_report_types;
+	hidg->wakeup_on_write = opts->wakeup_on_write;
 	hidg_scan_report_desc(hidg);
 
 	++opts->refcnt;
diff --git a/drivers/usb/gadget/function/u_hid.h b/drivers/usb/gadget/function/u_hid.h
index 0ede046..f7e8145 100644
--- a/drivers/usb/gadget/function/u_hid.h
+++ b/drivers/usb/gadget/function/u_hid.h
@@ -22,6 +22,7 @@ struct f_hid_opts {
 	unsigned char			protocol;
 	unsigned char			no_out_endpoint;
 	unsigned char			strict_report_types;
+	unsigned char			wakeup_on_write;
 	unsigned short			report_length;
 	unsigned short			report_desc_length;
 	unsigned char			*report_desc;
```

## kernel-patches/0005-usb-dwc2-composite-standard-request-answers-of-a-real-device.patch

`7228 bytes, 182 lines, sha256 4848d6b4b431498f4c37aafd4f1ed3e5c7405d71c44ec02ecbce1081c9cc8ebf`

```diff
From: hid-bridge project
Subject: [PATCH 5/5] usb: dwc2, composite: standard-request answers of a real bus-powered device

STATUS: written against rpi-6.12.y and verified to apply, NOT yet tested on
CM5 hardware.

Four standard-request behaviours differ from what a real bus-powered
keyboard does and are visible to a host or analyser issuing the requests:

- libcomposite marked the gadget self-powered at bind, so GET_STATUS(Device)
  reported Self Powered until the first SET_CONFIGURATION.  Report
  bus-powered until a configuration is selected; set_config() then follows
  the configuration's bmAttributes as before.
- dwc2 ACKed SET_FEATURE(DEVICE_REMOTE_WAKEUP) unconditionally and GET_STATUS
  reflected it even when the configuration did not advertise remote wakeup.
  Add the .set_remote_wakeup operation (called by libcomposite's set_config
  with the configuration's wakeup bit), STALL the feature request when the
  configuration does not support it, and clear both flags on bus reset
  (dwc2_hsotg_core_init_disconnected), as USB 2.0 section 9.1.1.6 requires.
- dwc2 entered USB 2.0 test modes at full speed; they exist for high-speed
  capable functions only, so STALL them when the gadget driver is limited
  to full speed.
- dwc2 answered GET_STATUS(Interface) with zero for any wIndex, configured
  or not.  Delegate to the gadget driver, and have libcomposite answer
  zero for an existing interface of the active configuration and STALL
  otherwise (USB 2.0 section 9.4.5) for USB 2.0 devices too.

---
diff --git a/drivers/usb/dwc2/core.h b/drivers/usb/dwc2/core.h
index 2bd74f3..9c3d991 100644
--- a/drivers/usb/dwc2/core.h
+++ b/drivers/usb/dwc2/core.h
@@ -1217,6 +1217,7 @@ struct dwc2_hsotg {
 	unsigned int enabled:1;
 	unsigned int connected:1;
 	unsigned int remote_wakeup_allowed:1;
+	unsigned int remote_wakeup_supported:1;
 	struct dwc2_hsotg_ep *eps_in[MAX_EPS_CHANNELS];
 	struct dwc2_hsotg_ep *eps_out[MAX_EPS_CHANNELS];
 #endif /* CONFIG_USB_DWC2_PERIPHERAL || CONFIG_USB_DWC2_DUAL_ROLE */
diff --git a/drivers/usb/dwc2/gadget.c b/drivers/usb/dwc2/gadget.c
index e650c7b..b43d424 100644
--- a/drivers/usb/dwc2/gadget.c
+++ b/drivers/usb/dwc2/gadget.c
@@ -1693,9 +1693,12 @@ static int dwc2_hsotg_process_req_status(struct dwc2_hsotg *hsotg,
 		break;
 
 	case USB_RECIP_INTERFACE:
-		/* currently, the data result should be zero */
-		reply = cpu_to_le16(0);
-		break;
+		/*
+		 * Only the gadget driver knows whether the interface exists
+		 * and whether the device is configured; let it answer (or
+		 * STALL) instead of replying zero for any wIndex.
+		 */
+		return 0;
 
 	case USB_RECIP_ENDPOINT:
 		ep = ep_from_windex(hsotg, le16_to_cpu(ctrl->wIndex));
@@ -1795,6 +1798,9 @@ static int dwc2_hsotg_process_req_feature(struct dwc2_hsotg *hsotg,
 	case USB_RECIP_DEVICE:
 		switch (wValue) {
 		case USB_DEVICE_REMOTE_WAKEUP:
+			/* Request Error unless the configuration supports it */
+			if (!hsotg->remote_wakeup_supported)
+				return -ENOENT;
 			if (set)
 				hsotg->remote_wakeup_allowed = 1;
 			else
@@ -1806,6 +1812,10 @@ static int dwc2_hsotg_process_req_feature(struct dwc2_hsotg *hsotg,
 				return -EINVAL;
 			if (!set)
 				return -EINVAL;
+			/* Test modes exist for high-speed capable functions only */
+			if (hsotg->driver &&
+			    hsotg->driver->max_speed < USB_SPEED_HIGH)
+				return -ENOENT;
 
 			hsotg->test_mode = wIndex >> 8;
 			break;
@@ -3321,6 +3331,12 @@ void dwc2_hsotg_disconnect(struct dwc2_hsotg *hsotg)
 
 	hsotg->connected = 0;
 	hsotg->test_mode = 0;
+	/* A bus reset returns the device to the default state: the host's
+	 * remote-wakeup enable is gone (USB 2.0 9.1.1.6), and so is the
+	 * configuration that supported it.
+	 */
+	hsotg->remote_wakeup_allowed = 0;
+	hsotg->remote_wakeup_supported = 0;
 
 	/* all endpoints should be shutdown */
 	for (ep = 0; ep < hsotg->num_of_eps; ep++) {
@@ -4891,6 +4907,25 @@ out:
 	return ret;
 }
 
+/**
+ * dwc2_hsotg_set_remote_wakeup - record whether the active configuration
+ * advertises remote wakeup (libcomposite calls this from set_config).
+ * @gadget: The usb gadget state
+ * @set: 1 if the configuration's bmAttributes has the remote-wakeup bit
+ */
+static int dwc2_hsotg_set_remote_wakeup(struct usb_gadget *gadget, int set)
+{
+	struct dwc2_hsotg *hsotg = to_hsotg(gadget);
+	unsigned long flags;
+
+	spin_lock_irqsave(&hsotg->lock, flags);
+	hsotg->remote_wakeup_supported = !!set;
+	if (!set)
+		hsotg->remote_wakeup_allowed = 0;
+	spin_unlock_irqrestore(&hsotg->lock, flags);
+	return 0;
+}
+
 static const struct usb_gadget_ops dwc2_hsotg_gadget_ops = {
 	.get_frame	= dwc2_hsotg_gadget_getframe,
 	.set_selfpowered	= dwc2_hsotg_set_selfpowered,
@@ -4898,6 +4933,7 @@ static const struct usb_gadget_ops dwc2_hsotg_gadget_ops = {
 	.udc_stop		= dwc2_hsotg_udc_stop,
 	.pullup                 = dwc2_hsotg_pullup,
 	.wakeup			= dwc2_hsotg_gadget_wakeup,
+	.set_remote_wakeup	= dwc2_hsotg_set_remote_wakeup,
 	.udc_set_speed		= dwc2_gadget_set_speed,
 	.vbus_session		= dwc2_hsotg_vbus_session,
 	.vbus_draw		= dwc2_hsotg_vbus_draw,
@@ -5119,6 +5155,7 @@ int dwc2_gadget_init(struct dwc2_hsotg *hsotg)
 	hsotg->gadget.name = dev_name(dev);
 	hsotg->gadget.otg_caps = &hsotg->params.otg_caps;
 	hsotg->remote_wakeup_allowed = 0;
+	hsotg->remote_wakeup_supported = 0;
 
 	if (hsotg->params.lpm)
 		hsotg->gadget.lpm_capable = true;
diff --git a/drivers/usb/gadget/composite.c b/drivers/usb/gadget/composite.c
index 88e890f..e5cf9a7 100644
--- a/drivers/usb/gadget/composite.c
+++ b/drivers/usb/gadget/composite.c
@@ -2014,16 +2014,19 @@ composite_setup(struct usb_gadget *gadget, const struct usb_ctrlrequest *ctrl)
 		 * Note: function driver should supply such cb only for the
 		 * first interface of the function
 		 */
-		if (!gadget_is_superspeed(gadget))
-			goto unknown;
 		if (ctrl->bRequestType != (USB_DIR_IN | USB_RECIP_INTERFACE))
 			goto unknown;
-		value = 2;	/* This is the length of the get_status reply */
-		put_unaligned_le16(0, req->buf);
+		/* USB 2.0 9.4.5: Request Error unless configured and the
+		 * interface exists; the reply is otherwise all zero.
+		 */
 		if (!cdev->config || intf >= MAX_CONFIG_INTERFACES)
-			break;
+			goto unknown;
 		f = cdev->config->interface[intf];
 		if (!f)
+			goto unknown;
+		value = 2;	/* This is the length of the get_status reply */
+		put_unaligned_le16(0, req->buf);
+		if (!gadget_is_superspeed(gadget))
 			break;
 
 		if (f->get_status) {
@@ -2472,12 +2475,11 @@ int composite_dev_prepare(struct usb_composite_driver *composite,
 	cdev->driver = composite;
 
 	/*
-	 * As per USB compliance update, a device that is actively drawing
-	 * more than 100mA from USB must report itself as bus-powered in
-	 * the GetStatus(DEVICE) call.
+	 * Report bus-powered until a configuration is selected; set_config()
+	 * then follows the configuration's bmAttributes.  A bus-powered
+	 * keyboard never claims to be self-powered in the Address state.
 	 */
-	if (CONFIG_USB_GADGET_VBUS_DRAW <= USB_SELF_POWER_VBUS_MAX_DRAW)
-		usb_gadget_set_selfpowered(gadget);
+	usb_gadget_clear_selfpowered(gadget);
 
 	/* interface and string IDs start at zero via kzalloc.
 	 * we force endpoints to start unassigned; few controller
```
