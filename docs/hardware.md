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
   Pi 5 family, and the kernel is told the device is bus-powered regardless.
2. **rpiboot straps.**  On the CM5 IO Board the USB-C jack doubles as the
   rpiboot/eMMC-flashing port.  Leave the "nRPIBOOT"/USB-boot jumper in its
   normal position, otherwise the module enumerates as a BCM boot device
   instead of running your OS.

If the PC is powered off, USB ports on many motherboards still supply 5 V and
keep the port idle rather than resetting it.  To the CM5 that looks like a
bus *suspend*, not a disconnect: `hid-bridge ctl status` shows
`backing_off: true` and reports wait for the PC to come back.  A port that
drops or resets shows `host_connected: false` instead.  Both are harmless.

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
