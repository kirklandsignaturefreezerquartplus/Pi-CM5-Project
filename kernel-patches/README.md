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
| `SET_FEATURE(DEVICE_REMOTE_WAKEUP)` when the configuration has no wakeup bit | ACKed and reflected in `GET_STATUS` | STALLed; flags cleared on bus reset (0005) |
| `SET_FEATURE(TEST_MODE)` at full speed | entered | STALLed: test modes are for high-speed capable functions (0005) |
| `GET_STATUS(Interface)` | zero for any wIndex, configured or not | zero for an existing interface of the active configuration, STALL otherwise (0005) |

The patches are generated from and verified against the `rpi-6.12.y` branch of
https://github.com/raspberrypi/linux.  They are small, affect only gadget
mode, and change nothing when `max_speed` is `high-speed` except 0001, 0003
and 0005's request handling.  **0004 and 0005 have not been exercised on
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
  low-speed path already uses 8) but not written, see
  `docs/review-analysis.md` item 3.
* `bInterval` fixed at 10 ms (full speed): typical for keyboards and cheap
  mice; adding a configfs attribute is a larger change than is warranted.
* `GET_IDLE` power-up default: HID 1.11 recommends 500 ms for keyboards,
  which would require the function to re-send reports periodically; 0
  matches what it does.
