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
