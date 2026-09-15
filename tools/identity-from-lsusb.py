#!/usr/bin/env python3
"""Turn an `lsusb -v` dump of a reference keyboard/mouse into a [gadget] block.

    lsusb -v -d 046d:c534 > reference.txt          # on any Linux machine
    tools/identity-from-lsusb.py reference.txt      # paste output into config.toml

Copies idVendor, idProduct, bcdDevice, manufacturer/product/serial strings
and the configuration power attributes.  The serial is deliberately
randomised (same length and character class as the original) so the CM5
never shares a serial with the physical unit.  Only the first device in the
dump is used.

It also compares the reference device's descriptor tree (bcdUSB, EP0 size,
interface count, class/subclass/protocol per interface, endpoints, polling
interval, packet size, HID version and report-descriptor length) with what
hid-bridge presents and prints a WARNING comment for every difference, so
you know in advance where a descriptor dump of the clone would not match the
original.
"""
from __future__ import annotations

import random
import re
import sys


def _field(text: str, name: str) -> str | None:
    match = re.search(rf"^\s*{name}\s+(\S+)(?:\s+(.*))?$", text, re.M)
    return match.group(1) if match else None


def _string_field(text: str, name: str) -> str:
    match = re.search(rf"^\s*{name}\s+(\d+)\s*(.*)$", text, re.M)
    if not match or match.group(1) == "0":
        return ""
    return match.group(2).strip()


def _randomise_serial(serial: str, rng: random.Random) -> str:
    out = []
    for ch in serial:
        if ch.isdigit():
            out.append(rng.choice("0123456789"))
        elif ch.isupper() and ch in "ABCDEF":
            out.append(rng.choice("ABCDEF"))
        elif ch.isupper():
            out.append(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ"))
        elif ch.islower():
            out.append(rng.choice("abcdefghijklmnopqrstuvwxyz"))
        else:
            out.append(ch)
    return "".join(out)


# What hid-bridge presents (full-speed, relative mouse, 3 buttons, boot
# keyboard descriptor).  See docs/usb-identity.md.
PRESENTED = {
    "bcdUSB": "2.00 (2.01 with LPM)",
    "bMaxPacketSize0": 64,
    "interfaces": [
        {"class": 3, "subclass": 1, "protocol": 1, "endpoints": 1, "bInterval": 10, "wMaxPacketSize": 8, "bcdHID": "1.01 (1.10 with kernel-patches/0001)", "report_len": 63},
        {"class": 3, "subclass": 1, "protocol": 2, "endpoints": 1, "bInterval": 10, "wMaxPacketSize": 4, "bcdHID": "1.01 (1.10 with kernel-patches/0001)", "report_len": 52},
    ],
}


def _interfaces(block: str) -> list[dict]:
    """Parse the Interface Descriptor blocks of an lsusb -v dump."""
    found = []
    parts = re.split(r"^\s*Interface Descriptor:\s*$", block, flags=re.M)
    for part in parts[1:]:
        # stop at the next interface/configuration boundary if any slipped through
        iface = {}
        for name in ("bInterfaceNumber", "bAlternateSetting", "bNumEndpoints", "bInterfaceClass",
                     "bInterfaceSubClass", "bInterfaceProtocol"):
            value = _field(part, name)
            iface[name] = int(value) if value and value.isdigit() else None
        hid = re.search(r"bcdHID\s+(\S+)", part)
        iface["bcdHID"] = hid.group(1) if hid else None
        rlen = re.search(r"wDescriptorLength\s+(\d+)", part)
        iface["report_len"] = int(rlen.group(1)) if rlen else None
        endpoints = []
        for ep in re.finditer(r"bEndpointAddress\s+0x([0-9a-fA-F]{2})\s+EP \d+ (IN|OUT).*?wMaxPacketSize\s+0x([0-9a-fA-F]{4}).*?bInterval\s+(\d+)", part, re.S):
            endpoints.append({"dir": ep.group(2), "wMaxPacketSize": int(ep.group(3), 16), "bInterval": int(ep.group(4))})
        iface["endpoints"] = endpoints
        found.append(iface)
    return found


def topology_warnings(block: str) -> list[str]:
    """Differences between the reference device and what hid-bridge presents."""
    warnings = []
    bcd_usb = _field(block, "bcdUSB")
    if bcd_usb and bcd_usb not in ("2.00", "2.01"):
        warnings.append(f"reference bcdUSB is {bcd_usb}; hid-bridge presents {PRESENTED['bcdUSB']} (kernel-fixed, see docs/usb-identity.md)")
    ep0 = _field(block, "bMaxPacketSize0")
    if ep0 and ep0.isdigit() and int(ep0) != PRESENTED["bMaxPacketSize0"]:
        warnings.append(f"reference bMaxPacketSize0 is {ep0}; hid-bridge presents {PRESENTED['bMaxPacketSize0']} (kernel-fixed)")
    ifaces = [i for i in _interfaces(block) if i.get("bAlternateSetting") in (0, None)]
    if not ifaces:
        warnings.append("no interface descriptors found in the dump (run lsusb -v as root to include them)")
        return warnings
    if len(ifaces) != len(PRESENTED["interfaces"]):
        warnings.append(f"reference has {len(ifaces)} interface(s); hid-bridge presents {len(PRESENTED['interfaces'])} (boot keyboard + boot mouse)")
    for index, (ref, ours) in enumerate(zip(ifaces, PRESENTED["interfaces"])):
        triple = (ref["bInterfaceClass"], ref["bInterfaceSubClass"], ref["bInterfaceProtocol"])
        if triple != (ours["class"], ours["subclass"], ours["protocol"]):
            warnings.append(f"interface {index}: reference class/subclass/protocol {triple}; hid-bridge presents "
                            f"({ours['class']}, {ours['subclass']}, {ours['protocol']})")
        if ref["bNumEndpoints"] is not None and ref["bNumEndpoints"] != ours["endpoints"]:
            warnings.append(f"interface {index}: reference has {ref['bNumEndpoints']} endpoint(s) (an interrupt OUT endpoint?); "
                            f"hid-bridge presents {ours['endpoints']} (LEDs via SET_REPORT on EP0)")
        for ep in ref["endpoints"]:
            if ep["dir"] == "IN":
                if ep["bInterval"] != ours["bInterval"]:
                    warnings.append(f"interface {index}: reference polls every {ep['bInterval']} ms; hid-bridge presents {ours['bInterval']} ms (kernel-fixed at full speed)")
                if ep["wMaxPacketSize"] != ours["wMaxPacketSize"]:
                    warnings.append(f"interface {index}: reference wMaxPacketSize {ep['wMaxPacketSize']}; hid-bridge presents {ours['wMaxPacketSize']} (= report length)")
        if ref["bcdHID"] and ref["bcdHID"] not in ("1.01", "1.10"):
            warnings.append(f"interface {index}: reference bcdHID {ref['bcdHID']}; hid-bridge presents {ours['bcdHID']}")
        elif ref["bcdHID"] == "1.10":
            warnings.append(f"interface {index}: reference bcdHID 1.10; hid-bridge presents 1.01 unless kernel-patches/0001 is installed")
        if ref["report_len"] is not None and ref["report_len"] != ours["report_len"]:
            warnings.append(f"interface {index}: reference report descriptor is {ref['report_len']} bytes; hid-bridge presents {ours['report_len']} "
                            f"(use `usbhid-dump` to compare the bytes; hid-bridge's are spec-exact, not a copy)")
    return warnings


def convert(dump: str, rng: random.Random | None = None) -> str:
    rng = rng or random.Random()
    # Restrict to the first device block.
    parts = re.split(r"^Bus \d+ Device \d+: ID ", dump, flags=re.M)
    block = parts[1] if len(parts) > 1 else dump

    vid = _field(block, "idVendor")
    pid = _field(block, "idProduct")
    bcd = _field(block, "bcdDevice")
    if not (vid and pid):
        raise SystemExit("could not find idVendor/idProduct in the dump")
    manufacturer = _string_field(block, "iManufacturer")
    product = _string_field(block, "iProduct")
    serial = _string_field(block, "iSerial")
    attrs_match = re.search(r"^\s*bmAttributes\s+0x([0-9a-fA-F]{2})\s*$", block, re.M)
    attrs = int(attrs_match.group(1), 16) if attrs_match else 0xA0
    max_power_match = re.search(r"^\s*(?:MaxPower|bMaxPower)\s+(\d+)mA", block, re.M)
    max_power = int(max_power_match.group(1)) if max_power_match else 100
    bcd_value = int(bcd.replace(".", ""), 16) if bcd else 0x0100

    lines = [
        "[gadget]",
        'name = "hidbridge"',
        f"vendor_id = {vid}",
        f"product_id = {pid}",
        f"device_version = 0x{bcd_value:04x}",
        f'manufacturer = "{manufacturer}"',
        f'product = "{product}"',
        f'serial = "{_randomise_serial(serial, rng)}"' if serial else 'serial = ""',
        'max_speed = "full-speed"',
        f"self_powered = {'true' if attrs & 0x40 else 'false'}",
        f"remote_wakeup = {'true' if attrs & 0x20 else 'false'}",
        f"max_power_ma = {max(1, min(500, max_power))}",
        'udc = ""',
    ]
    notes = []
    if not serial:
        notes.append("# reference has no serial; set all three strings or none (see docs/usb-identity.md)")
    if not (manufacturer or product):
        notes.append("# reference has no strings at all: leave manufacturer/product/serial empty")
    for warning in topology_warnings(block):
        notes.append(f"# WARNING: {warning}")
    if any(n.startswith("# WARNING") for n in notes):
        notes.append("# A descriptor dump of the clone will differ from the original in the points above;")
        notes.append("# pick a reference with matching topology if that matters (docs/remaining-tells.md).")
    return "\n".join(lines + notes) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8", errors="replace") as fh:
        sys.stdout.write(convert(fh.read()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
