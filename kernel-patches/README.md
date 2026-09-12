# Optional kernel patches: remove the last Linux-gadget tells

Everything `hid-bridge` can pin from user space is pinned.  Five details are
decided inside the kernel and remain visible to a descriptor dumper or USB
analyser (never to Windows or UEFI, which do not look at them):

| Tell | Stock rpi-6.12.y | With these patches |
|---|---|---|
| HID descriptor `bcdHID` | 1.01 (obsolete; a Linux `usb_f_hid` signature) | 1.10, like real keyboards |
| `GET_IDLE` default | 1 (4 ms) although nothing is ever re-sent | 0 (report on change), consistent |
| At full speed: `DEVICE_QUALIFIER` / `OTHER_SPEED_CONFIGURATION` | answered (device claims high-speed capability it never used) | STALLed, like every full-speed-only keyboard |
| At full speed: `bcdUSB` / BOS when the dwc2 core has LPM enabled | 2.01 + BOS with an LPM capability | 2.00, no BOS |
| `GET_REPORT` for Output/Feature, `SET_REPORT` for Input/Feature | answered / accepted regardless of report type | STALLed via the new `strict_report_types` attribute (0003), which `hid-bridge gadget up` enables when present |
| Remote wakeup | bit advertised, key press never wakes a suspended host (dwc2 has no `.wakeup`) | 0004 adds the dwc2 `.wakeup` operation and an f_hid `wakeup_on_write` attribute that `hid-bridge gadget up` enables. **0004 applies cleanly but is untested on hardware**; see `docs/remaining-tells.md` §3 for the test procedure |

The patches are generated from and verified against the `rpi-6.12.y` branch of
https://github.com/raspberrypi/linux.  They are small, affect only gadget
mode, and change nothing when `max_speed` is `high-speed`.

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

Check with `uname -r` (custom version suffix) and `tools/verify-gadget.sh`.
If the branch has moved and a patch no longer applies, the hunks are a few
lines each; the intent is documented in each patch header.

Keep the patched kernel from being replaced: `sudo apt-mark hold
linux-image-rpi-2712 linux-image-rpi-v8` (package names vary by release), or
rebuild after each kernel update.  Cross-compiling from a PC follows the
official Raspberry Pi kernel documentation with the same `git apply` step.

## What the patches do not touch

* `bMaxPacketSize0 = 64`: physically true for the dwc2 controller; many real
  full-speed keyboards report 64 as well.
* `bInterval` fixed at 10 ms (full speed): typical for keyboards and cheap
  mice; adding a configfs attribute is a larger change than is warranted.
* `bcdUSB`/EP0 when running at high speed: already self-consistent.
