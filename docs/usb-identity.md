# USB identity: what is pinned, what the kernel fixes, how to verify

The requirement is that the PC sees **only a simple generic keyboard and
mouse, down to the USB handshake**.  This document is the honest accounting of
that requirement against what Linux's `libcomposite`/`usb_f_hid`/`dwc2`
stack lets user space control.

## Pinned by hid-bridge (configfs)

| Descriptor / behaviour | Value | Notes |
|---|---|---|
| Link speed | full-speed only (`max_speed = "full-speed"`) | dwc2 is told not to chirp; the host never sees a high-speed capable device and a `GET_DESCRIPTOR(DEVICE_QUALIFIER)` is STALLed, exactly like a USB 1.1 device. |
| bDeviceClass/SubClass/Protocol | 0/0/0 | class defined at interface level |
| idVendor / idProduct / bcdDevice | configurable | Windows and UEFI bind boot HID by class; the IDs only affect Device Manager's hardware ID strings. |
| iManufacturer / iProduct | "Generic" / "USB Keyboard" (configurable) | |
| iSerialNumber | 0 (none) unless `gadget.serial` is set | most inexpensive keyboards have none |
| iConfiguration / iInterface | 0 | never set |
| bNumConfigurations | 1 | |
| Configuration bmAttributes / MaxPower | 0xA0 (bus powered + remote wakeup), 100 mA | configurable |
| Interfaces | 2: HID boot keyboard, HID boot mouse | link order fixes interface numbers 0 and 1 |
| Endpoints | one interrupt IN per interface | `no_out_endpoint = 1` (kernel ≥ 5.16): LED output travels over EP0 `SET_REPORT`, as with real boot keyboards |
| HID class descriptor | bcdHID 1.11, bCountryCode 0, one report descriptor | as emitted by `usb_f_hid` |
| Report descriptor (keyboard) | 63 bytes, HID 1.11 App. E.6 | `keyboard.descriptor = "boot"`; unit test asserts byte equality |
| Report descriptor (mouse) | boot mouse + wheel | first 3 report bytes are the boot format |
| Report IDs | none | |
| bInterval | keyboard 10 ms, mouse 2 ms | applied when the kernel exposes the f_hid `interval` attribute (6.x); otherwise f_hid's default of 10 ms applies to both |
| Remote wakeup | asserted on first write after suspend | `wakeup_on_write` attribute where available |
| GET/SET_PROTOCOL, GET/SET_IDLE | handled by `usb_f_hid` | a BIOS switching to boot protocol keeps working because our reports already are boot format |
| Microsoft OS string descriptor (index 0xEE) | STALL | `os_desc` is never configured |
| OTG descriptor | absent | requires `dr_mode=peripheral`, which `install.sh` sets |
| BOS / WebUSB / LPM capability | not requested | see kernel-fixed fields below |

## Fixed by the kernel (cannot be changed from user space)

| Field | What a USB 1.1 keyboard reports | What the CM5 reports | Why |
|---|---|---|---|
| bcdUSB | 0x0110 | 0x0200, or 0x0201/0x0210 with a BOS descriptor | `composite.c` overwrites the configfs `bcdUSB` value from the gadget's capabilities; if `dwc2` marks the gadget `lpm_capable`, libcomposite advertises USB 2.0 LPM through a BOS descriptor. |
| bMaxPacketSize0 | 8 | 64 | `composite.c` copies the controller's EP0 size; dwc2 uses 64. |
| Endpoint addresses | vendor-specific | 0x81, 0x82 | allocated by the controller; the same as most real two-interface combos |
| Hub-level electrical signalling | FS | FS | identical: no chirp, 12 Mbit/s, D+ pull-up |

Both deviations are common in genuine full-speed keyboards sold today (many
report bcdUSB 2.00 and an EP0 size of 64), and neither is inspected by
Windows' HID class drivers or by UEFI boot-keyboard drivers.  They are only
visible to a protocol analyser or a descriptor dumper.

If a byte-exact `bcdUSB = 0x0110` / `bMaxPacketSize0 = 8` is required anyway,
the options are:

1. **Kernel patch** — in `drivers/usb/gadget/composite.c` (`composite_setup`,
   `USB_DT_DEVICE` case) honour the descriptor values written through configfs
   instead of recomputing them, and in `drivers/usb/gadget/udc/dwc2` clear
   `gadget.lpm_capable`.  Raspberry Pi OS kernels rebuild in an hour on the
   CM5 itself.
2. **raw-gadget** (`CONFIG_USB_RAW_GADGET`) — user space answers every control
   request itself, so every descriptor byte is yours.  It is a rewrite of the
   gadget half of this project and forgoes `usb_f_hid`'s boot-protocol
   handling, so it is documented as a future path rather than implemented.

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
Descriptor Dumper**.  Check: `bcdUSB`, `bDeviceClass 0`, one configuration,
`bmAttributes 0xA0`, two interfaces of class 3 with subclass 1 and protocols 1
and 2, one interrupt IN endpoint each, and the report descriptors matching the
hex printed by `hid-bridge check` on the CM5.

### Linux host

```sh
lsusb -d 1209:0001 -v            # descriptors
sudo usbhid-dump -d 1209:0001    # raw report descriptors
```

`lsusb -t` should show the device under an EHCI/xHCI root at **12M**.

### On the CM5

```sh
tools/verify-gadget.sh          # configfs values, UDC state and speed, hidg nodes
hid-bridge gadget status        # same as JSON
```

`state` must read `configured` and `current_speed` `full-speed` while the PC
is on.

## UEFI / pre-boot behaviour

UEFI keyboard drivers require: class 3, subclass 1 (boot), protocol 1, an
interrupt IN endpoint, and 8-byte boot reports — all satisfied.  Firmware that
issues `SET_PROTOCOL(boot)` gets identical reports.  Mouse support in setup
menus additionally needs protocol 2 with 3-byte boot reports, which the
default `mouse.mode = "relative"` provides.  The `absolute` mode is a tablet
style pointer, which firmware ignores; use it only when the OS is running.
