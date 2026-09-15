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

The source is not grabbed (`grab_inputs = false` or the grab failed).  Look
for "cannot grab" in the journal; another process (e.g. a desktop session)
holds the device.  Run Raspberry Pi OS **Lite** on the CM5 and keep
`grab_inputs = true`.

## Nothing typed on the PC, bridge says host_connected: false

`hid-bridge ctl status` → `keyboard.host_connected: false` means writes fail
with ESHUTDOWN: the PC has not configured the device.  See the UDC section
above.  Reports are dropped, not queued, until it does.

## `deferred` keeps rising, or `backing_off: true`, in `hid-bridge ctl status`

`deferred` counts writes that had to wait for the host's next poll; a fast
mouse stream makes it rise normally.  `backing_off: true` means the host has
suspended the bus (PC asleep, or the OS selectively suspended the keyboard):
dwc2 refuses reports until the host resumes, so the bridge retries with a
growing delay and keeps the current key state for the resume.  A key press
only wakes the PC with `kernel-patches/0004` installed; wake it by other
means otherwise.  Motion made while the PC sleeps is discarded, as a real
mouse's would be.

## A key seems stuck on the PC

```sh
hid-bridge ctl release-all
```

Then check which source held it: `hid-bridge ctl inputs` lists `keys_held`
per source.  Unplugging a source always releases its keys.

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
the bridge notices the recreated `/dev/hidg*` nodes within a second and
reopens them.)

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
  Ethernet functions, for instance) are listed as ignored by design.

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
