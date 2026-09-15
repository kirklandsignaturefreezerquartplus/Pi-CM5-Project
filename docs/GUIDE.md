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
| **Boot protocol** | The simplest keyboard/mouse report format, understood by every BIOS/UEFI. The bridge always speaks it. |
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
newer works; the notes in `docs/usb-identity.md` are written against 6.12.

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
Ran 101 tests in 0.1s

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
4. Adds one line to `/boot/firmware/config.txt`:
   `dtoverlay=dwc2,dr_mode=peripheral`.  This switches the USB-C connector
   into device mode.  A backup of the file is kept next to it.
5. Installs and enables two services: `hid-gadget` (creates the virtual
   keyboard/mouse at boot) and `hid-bridge` (forwards input).
6. Runs `hid-bridge check` and prints the descriptors.  Two `note:` lines
   about the test vendor ID and about strings are normal at this stage.
7. Ends with `Reboot to activate USB device mode:  sudo reboot`.

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

Expected: a line like `attached /dev/input/event0: 'Dell KB216 ...' kbd=True
mouse=False ... role=passthrough (default passthrough) grabbed`.

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

Expected: `"keyboard": {"sent": <some number>, "dropped": 0, "host_connected": true}`,
your keyboard listed under `"sources"`, and `"leds": 2` while Caps Lock is on.

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
| bcdUSB | 2.00 (or 2.01 with a BOS descriptor if `lpm (debugfs)` shows 1 on the CM5) |
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

Afterwards `hid-bridge check` reports `kernel-patches/ present: yes`, no
longer lists `strict_report_types` or `wakeup_on_write` as missing, and
`tools/verify-gadget.sh` shows them set to 1.  The remote-wakeup operation
can be exercised without a key press: `echo 1 | sudo tee
/sys/class/udc/*/srp` while the target sleeps.  Hold the kernel package so an update does not replace it:

```sh
apt-mark showhold; dpkg -l | grep linux-image    # find the installed package name
sudo apt-mark hold <that package>
```

If the CM5 fails to boot on the new kernel, put the SD/eMMC into another
machine (or use rpiboot) and rename `kernel_2712-stock.img` back to
`kernel_2712.img`.

Patch 0004 (remote wakeup) has not yet been exercised on hardware.  Test it
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
Consider `macro_jitter_ms = 40` under `[bridge]` so typed macros do not have a
perfectly regular rhythm.

### 10.3 A macro keypad

1. Plug the keypad into a spare USB-A port on the CM5.
2. `hid-bridge inputs` shows it, for example
   `Macro Pad  1a2c:2d43  keyboard  passthrough`.  Right now its keys would
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
| `host_connected: false` in `ctl status` | Target off, asleep, or not enumerated; reports are dropped until it returns |
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
tools/identity-from-lsusb.py FILE    build a [gadget] block from a reference device
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
