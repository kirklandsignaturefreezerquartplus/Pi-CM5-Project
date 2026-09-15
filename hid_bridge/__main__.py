"""Command line entry point: ``python3 -m hid_bridge <command>``."""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from . import __version__
from .config import ConfigError, load_config
from .descriptors import report_bit_sizes


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _hexdump(data: bytes, width: int = 16) -> str:
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        lines.append("  " + " ".join(f"{b:02x}" for b in chunk))
    return "\n".join(lines)


def cmd_gadget(args, cfg) -> int:
    from .gadget import Gadget, GadgetError
    gadget = Gadget(cfg)
    try:
        if args.action == "up":
            devices = gadget.up()
            print(json.dumps(devices, indent=2))
            for warning in gadget.warnings:
                print(f"warning: {warning}", file=sys.stderr)
        elif args.action == "down":
            gadget.down()
        elif args.action == "status":
            print(json.dumps(gadget.status(), indent=2))
    except GadgetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_run(args, cfg) -> int:
    from .bridge import Bridge
    from .gadget import Gadget, GadgetError, load_state
    devices = load_state()
    if devices is None or not all(os.path.exists(devices.get(k, "")) for k in ("keyboard", "mouse")):
        gadget = Gadget(cfg)
        try:
            if gadget.exists() and gadget.bound_udc():
                devices = gadget.resolve_devices()
            elif args.auto_gadget:
                devices = gadget.up()
            else:
                print("error: gadget is not up; run 'hid-bridge gadget up' first (or use --auto-gadget)", file=sys.stderr)
                return 1
        except GadgetError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    Bridge(cfg, devices).run()
    return 0


def cmd_inputs(args, cfg) -> int:
    from .linux_input import InputDevice, list_event_nodes
    rows = []
    for path in list_event_nodes():
        try:
            dev = InputDevice(path)
        except OSError as exc:
            rows.append((path, f"<cannot open: {exc.strerror}>", "", "", ""))
            continue
        try:
            ident = dev.identity
            rule = cfg.rule_for(ident.name, ident.phys, ident.vendor, ident.product)
            kinds = []
            if dev.is_keyboard:
                kinds.append("keyboard")
            if dev.is_mouse:
                kinds.append("mouse(abs)" if dev.has_abs_pointer else "mouse")
            role = rule.role if kinds else "ignored (not kbd/mouse)"
            rows.append((path, ident.name, f"{ident.vendor:04x}:{ident.product:04x}", ",".join(kinds) or "-", f"{role} [{rule.describe()}]"))
        finally:
            dev.close()
    if not rows:
        print("no /dev/input/event* devices found")
        return 0
    widths = [max(len(str(r[i])) for r in rows + [("PATH", "NAME", "ID", "KIND", "ROLE")]) for i in range(5)]
    header = ("PATH", "NAME", "ID", "KIND", "ROLE")
    for row in [header] + rows:
        print("  ".join(str(col).ljust(widths[i]) for i, col in enumerate(row)).rstrip())
    return 0


def cmd_check(args, cfg) -> int:
    from .descriptors import KEYBOARD_REPORT_LENGTH, keyboard_report_descriptor, mouse_report_descriptor, mouse_report_length
    from .gadget import Gadget, list_udcs

    ok = True
    print(f"config: {cfg.path or '(defaults)'}")
    g = cfg.gadget
    print(f"device: idVendor=0x{g.vendor_id:04x} idProduct=0x{g.product_id:04x} bcdDevice=0x{g.device_version:04x} "
          f"max_speed={g.max_speed} strings={'/'.join(filter(None, (g.manufacturer, g.product, g.serial))) or '(none)'}")
    attrs = 0x80 | (0x40 if g.self_powered else 0) | (0x20 if g.remote_wakeup else 0)
    print(f"config: bmAttributes=0x{attrs:02x} MaxPower={g.max_power_ma}mA, 2 interfaces (HID keyboard, HID mouse)")
    if (g.vendor_id, g.product_id) == (0x1209, 0x0001):
        print("  note: 0x1209:0x0001 is the pid.codes *test* ID; USB ID databases (lsusb, USBView) label it as such."
              " Choose your own IDs in [gadget] if the device must not read as a test/hobby device")
    strings_set = [bool(g.manufacturer), bool(g.product), bool(g.serial)]
    if any(strings_set) and not all(strings_set):
        print("  note: set all of manufacturer/product/serial or none; an unset one becomes an empty string descriptor"
              " (install.sh fills in a random serial on first install)")
    print("kernel-fixed on a stock kernel: bcdUSB 0x0200 (0x0201 + BOS when the controller enables LPM), "
          "bMaxPacketSize0 64, bcdHID 1.01, bInterval 10 ms at full speed / 1 ms at high speed")
    print("with kernel-patches/ installed: bcdHID 1.10, bcdUSB 0x0200 without BOS at full speed, GET_IDLE 0, "
          "report-type checks, remote wakeup; bMaxPacketSize0 and bInterval unchanged")

    kbd = keyboard_report_descriptor(cfg.keyboard.descriptor == "extended")
    in_bits, out_bits = report_bit_sizes(kbd)
    print(f"\nkeyboard descriptor ({cfg.keyboard.descriptor}, {len(kbd)} bytes): input {in_bits // 8} bytes, output {out_bits // 8} byte(s)")
    print(_hexdump(kbd))
    if in_bits != KEYBOARD_REPORT_LENGTH * 8:
        print("  ERROR: keyboard report length mismatch")
        ok = False

    mouse = mouse_report_descriptor(cfg.mouse.mode, cfg.mouse.buttons)
    in_bits, out_bits = report_bit_sizes(mouse)
    print(f"\nmouse descriptor ({cfg.mouse.mode}, {cfg.mouse.buttons} buttons, {len(mouse)} bytes): input {in_bits // 8} bytes")
    print(_hexdump(mouse))
    if in_bits != mouse_report_length(cfg.mouse.mode) * 8:
        print("  ERROR: mouse report length mismatch")
        ok = False

    print(f"\nmacros defined: {', '.join(sorted(cfg.macros)) or '(none)'}")
    print(f"input rules: {len(cfg.inputs)}")
    for i, rule in enumerate(cfg.inputs):
        print(f"  [{i}] {rule.describe()} -> {rule.role}" + (f", {len(rule.bindings)} binding(s)" if rule.bindings else ""))

    print("\nkernel / platform:")
    udcs = list_udcs()
    print(f"  UDCs: {', '.join(udcs) if udcs else 'none (dwc2 overlay missing or not in peripheral mode?)'}")
    print(f"  configfs usb_gadget: {'present' if os.path.isdir(g.configfs) else 'missing (modprobe libcomposite)'}")
    for candidate in ("/boot/firmware/config.txt", "/boot/config.txt"):
        if os.path.exists(candidate):
            try:
                with open(candidate) as fh:
                    text = fh.read()
            except OSError:
                text = ""
            has = any(line.strip().startswith("dtoverlay=dwc2") for line in text.splitlines())
            print(f"  {candidate}: dwc2 overlay {'configured' if has else 'NOT configured'}")
            break
    gadget = Gadget(cfg)
    if gadget.exists():
        st = gadget.status()
        print(f"  gadget {g.name}: {'bound to ' + st['udc']['udc'] + ', host state ' + st['udc']['state'] + ', speed ' + st['udc']['current_speed'] if st.get('bound') else 'present, unbound'}")
        print(f"  kernel-patches/ present: {'yes (strict_report_types attribute found)' if st.get('patched_kernel') else 'no'}")
        if st.get("bound"):
            print(f"  controller LPM: {st['udc']['lpm']} -> device descriptor bcdUSB on the wire: {st['udc']['bcdUSB_on_wire']}")
        for role, func in st.get("functions", {}).items():
            missing = [k for k in ("no_out_endpoint", "strict_report_types", "wakeup_on_write", "interval") if func.get(k) == "n/a"]
            if missing:
                print(f"  {role}: kernel lacks optional f_hid attribute(s): {', '.join(missing)}")
    else:
        print(f"  gadget {g.name}: not created")
    print("\nOK" if ok else "\nPROBLEMS FOUND")
    return 0 if ok else 1


def cmd_ctl(args, cfg) -> int:
    from .control import send_request
    if args.what == "status":
        request = {"cmd": "status"}
    elif args.what == "inputs":
        request = {"cmd": "inputs"}
    elif args.what == "macro":
        request = {"cmd": "macro", "name": args.value[0] if args.value else ""}
    elif args.what == "type":
        request = {"cmd": "type", "text": " ".join(args.value)}
    elif args.what == "keys":
        request = {"cmd": "keys", "combo": " ".join(args.value)}
    elif args.what == "steps":
        request = {"cmd": "steps", "steps": args.value}
    elif args.what == "release-all":
        request = {"cmd": "release_all"}
    else:  # pragma: no cover
        raise SystemExit(f"unknown ctl command {args.what}")
    try:
        reply = send_request(cfg.bridge.control_socket, request)
    except (OSError, ConnectionError) as exc:
        print(f"error: cannot reach hid-bridge at {cfg.bridge.control_socket}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(reply, indent=2))
    return 0 if reply.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hid-bridge", description="CM5 USB HID keyboard/mouse bridge")
    parser.add_argument("-c", "--config", help="config file (default: $HID_BRIDGE_CONFIG or /etc/hid-bridge/config.toml)")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    parser.add_argument("--version", action="version", version=f"hid-bridge {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("gadget", help="create/remove/inspect the USB gadget")
    p.add_argument("action", choices=("up", "down", "status"))
    p.set_defaults(func=cmd_gadget)

    p = sub.add_parser("run", help="run the bridge daemon")
    p.add_argument("--auto-gadget", action="store_true", help="bring the gadget up if it is not")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("inputs", help="list input devices and how they would be handled")
    p.set_defaults(func=cmd_inputs)

    p = sub.add_parser("check", help="validate the configuration and show what the host will see")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("ctl", help="talk to the running bridge")
    p.add_argument("what", choices=("status", "inputs", "macro", "type", "keys", "steps", "release-all"))
    p.add_argument("value", nargs="*")
    p.set_defaults(func=cmd_ctl)

    args = parser.parse_args(argv)
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    _setup_logging("debug" if args.verbose else cfg.bridge.log_level)
    return args.func(args, cfg)


if __name__ == "__main__":
    sys.exit(main())
