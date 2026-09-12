#!/usr/bin/env python3
"""Turn an `lsusb -v` dump of a reference keyboard/mouse into a [gadget] block.

    lsusb -v -d 046d:c534 > reference.txt          # on any Linux machine
    tools/identity-from-lsusb.py reference.txt      # paste output into config.toml

Copies idVendor, idProduct, bcdDevice, manufacturer/product/serial strings
and the configuration power attributes.  The serial is deliberately
randomised (same length and character class as the original) so the CM5
never shares a serial with the physical unit.  Only the first device in the
dump is used.
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
