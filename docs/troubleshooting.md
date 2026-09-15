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
