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
| iConfiguration / iInterface | 0 | never set |
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
| bcdHID | 0x0110 | 0x0101 | constant in `usb_f_hid` |
| bInterval | 8–10 ms (FS) | 10 ms at full speed, 1 ms at high speed | constants in `usb_f_hid`; the `poll_interval_ms` options only take effect on kernels that add an `interval` attribute |
| DEVICE_QUALIFIER / OTHER_SPEED_CONFIGURATION at full speed | STALL (FS-only device) | answered (qualifier says high-speed capable) | `gadget->max_speed` stays HIGH because dwc2 does not read a DT `maximum-speed`; only `params.speed` is lowered; STALLed with `kernel-patches/0002` |
| Remote wakeup | bit advertised and functional | bit advertised, **not functional** on a stock kernel | dwc2's gadget ops have no `.wakeup` and `usb_f_hid` has no `wakeup_on_write` in 6.12; `kernel-patches/0004` adds both |
| iInterface | 0 | string index pointing at "HID Interface" | constant in `usb_f_hid`; `kernel-patches/0001` |
| `GET_STATUS(Device)` in the Address state | bus-powered | self-powered | `composite_bind` sets it at bind; `kernel-patches/0005` |
| `SET_FEATURE(REMOTE_WAKEUP)` with `remote_wakeup = false` | Request Error | ACKed | dwc2 has no `.set_remote_wakeup`; `kernel-patches/0005` |
| `SET_FEATURE(TEST_MODE)` at full speed | Request Error | entered | dwc2; `kernel-patches/0005` |
| `GET_STATUS(Interface 9)` | Request Error | 0x0000 | dwc2 answers without checking; `kernel-patches/0005` |
| `GET_IDLE` before the host's `SET_IDLE` | 125 (500 ms) recommended | 1 on stock, 0 with `kernel-patches/0001` | documented deviation; a 500 ms rate would require periodic re-sends |
| Interrupt IN transactions per report | 1 | 2 (report, then a zero-length packet) | `f_hidg_write` sets `req->zero`; `kernel-patches/0001` |
| Unset strings | absent (index 0) | index allocated, empty string descriptor | `libcomposite` substitutes "" for unset strings once the language directory exists |

Windows' HID class drivers and UEFI boot-keyboard drivers inspect none of
these; all of them are common in genuine USB 2.0 full-speed keyboards sold
today except the qualifier answer, which every host tolerates (a high-speed
capable device attached at full speed is a legal state).  They are visible
only to a descriptor dumper or a protocol analyser.

`hid-bridge check` and `tools/verify-gadget.sh` read dwc2's debugfs
`params` to tell you whether LPM is on, i.e. whether the wire shows 2.00 or
2.01 + BOS.

If a byte-exact match is required anyway, the routes are a kernel patch
(honour the configfs `bcdUSB`/`bMaxPacketSize0` in `composite_setup`, set
`gadget.max_speed` from `params.speed` in `dwc2_gadget_init`, clear
`lpm_capable`) or `raw-gadget`, where user space answers every control
request itself.  Both are outside this project.

## Deep inspection: what could still give the CM5 away

Assume an inspector with a hardware USB analyser, a descriptor dumper and a
USB ID database.  Nothing on the bus says "Raspberry Pi" or "Linux"; the
residual tells are indirect:

| Tell | Who sees it | Status |
|---|---|---|
| `bcdHID 1.01`, `GET_IDLE = 1`, qualifier answered at full speed, `bcdUSB 2.01` + BOS when LPM is on: together they fingerprint "Linux `usb_f_hid` on a dwc2 controller", i.e. a Raspberry Pi class board | analyser / dumper | **fixed by `kernel-patches/`** (kernel rebuild required) |
| VID:PID `1209:0001` resolves to "pid.codes Test PID" in `usb.ids` | `lsusb`, USBView, any ID lookup | **your decision**: set `gadget.vendor_id/product_id`; `hid-bridge check` reminds you while the test ID is in use |
| `GET_REPORT`/`SET_REPORT` for the *Feature* report type are accepted (real boot keyboards STALL them); `SET_REPORT` of any type lands in the LED path | analyser sending malformed class requests | **fixed by `kernel-patches/0003`** (`strict_report_types`, enabled automatically by `hid-bridge gadget up` when present); on a stock kernel the bridge additionally ignores any non-1-byte report in the LED path |
| Remote wakeup advertised but a key press does not wake a suspended PC | functional test | **`kernel-patches/0004`** (dwc2 `.wakeup` + f_hid `wakeup_on_write`; applies cleanly, untested on hardware); otherwise set `remote_wakeup = false` |
| VBUS current ≈ 0 mA while declaring bus-powered 100 mA | USB power meter | hardware: the CM5 runs from its own supply |
| The keyboard appears 15–25 s after the CM5 gets power and disconnects/reconnects whenever the CM5 or `hid-gadget.service` restarts | anyone watching enumeration | operational: power the CM5 before the PC, do not reboot it mid-session |
| With the nRPIBOOT strap fitted (or boot media missing on some carriers) the BCM2712 boot ROM enumerates as a Broadcom boot device (`0a5c:2712`) on the same port | anyone | hardware: keep nRPIBOOT unfitted and boot media reliable |
| Macro `type` steps with a fixed cadence, or modifier and key landing in the same report, look machine-generated | timing / report-sequence analysis of typed text | modifiers now lead and follow the key in their own reports; `bridge.macro_jitter_ms` (default 30) adds right-skewed jitter |
| D+ pull-up present while the PC port is unpowered, and attach with zero delay after port power-on (with the VBUS-blocking adapter the CM5 never sees the PC's 5 V) | meter on D+ with the port off; analyser timing VBUS-on to attach | hardware/operational: sense the PC's VBUS on a CM5 GPIO and drive `/sys/class/udc/<udc>/soft_connect`; see `docs/remaining-tells.md` §6 |
| A `GET_REPORT` arriving while `hid-bridge.service` is stopped is answered after 2.5 s with zeros | analyser, only in that window | `hid-bridge gadget up` now primes the GET_REPORT cache itself |

Recommended solves for every row that is not purely software are in
`docs/remaining-tells.md`.

Everything else — descriptors, report formats, boot-protocol handling,
`GET_REPORT` answers, LED handling, string set, endpoint layout — matches a
real two-interface keyboard/mouse device.

## Speed choice

* **full-speed** (default): 12 Mbit/s like real keyboards and mice, 10 ms
  polling, boot-protocol behaviour identical to a real FS device.  Deviation:
  the qualifier answer above.
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
