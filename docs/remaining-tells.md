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
sudo tee /sys/class/udc/*/srp` calls it directly.

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
   bound and the PC sees nothing.  Disable unattended reboots on the CM5
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
0x0409 only, `GET_IDLE` returning 0 before the host sets an idle rate, and
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
