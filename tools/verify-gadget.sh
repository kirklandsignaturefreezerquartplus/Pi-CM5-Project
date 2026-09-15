#!/bin/sh
# Dump everything the CM5 knows about its own gadget: configfs values, UDC
# state/speed and the hidg device nodes.  Run on the CM5 while it is plugged
# into the target.  Pair it with the host-side checks in docs/usb-identity.md.
G=${1:-/sys/kernel/config/usb_gadget/hidbridge}
echo "== gadget: $G"
[ -d "$G" ] || { echo "gadget not created (systemctl status hid-gadget)"; exit 1; }
for a in idVendor idProduct bcdDevice bcdUSB bDeviceClass bDeviceSubClass bDeviceProtocol bMaxPacketSize0 max_speed UDC; do
    printf '  %-18s %s\n' "$a" "$(cat "$G/$a" 2>/dev/null || echo n/a)"
done
echo "== strings"
for a in manufacturer product serialnumber; do
    printf '  %-18s %s\n' "$a" "$(cat "$G/strings/0x409/$a" 2>/dev/null || echo '(unset)')"
done
echo "== configuration c.1"
for a in bmAttributes MaxPower; do
    printf '  %-18s %s\n' "$a" "$(cat "$G/configs/c.1/$a" 2>/dev/null)"
done
echo "  interfaces (link order = interface number):"
ls -1 "$G/configs/c.1" | grep -v '^strings$' | grep -v '^bmAttributes$' | grep -v '^MaxPower$' | sed 's/^/    /'
for f in "$G"/functions/*; do
    echo "== function $(basename "$f")"
    for a in protocol subclass report_length no_out_endpoint strict_report_types wakeup_on_write interval dev; do
        printf '  %-18s %s\n' "$a" "$(cat "$f/$a" 2>/dev/null || echo n/a)"
    done
    printf '  %-18s %s\n' "report_desc" "$(xxd -p "$f/report_desc" 2>/dev/null | tr -d '\n' || od -An -tx1 "$f/report_desc" | tr -d ' \n')"
done
UDC=$(cat "$G/UDC" 2>/dev/null)
if [ -n "$UDC" ]; then
    echo "== UDC $UDC"
    for a in state current_speed maximum_speed is_a_peripheral function; do
        printf '  %-18s %s\n' "$a" "$(cat "/sys/class/udc/$UDC/$a" 2>/dev/null || echo n/a)"
    done
    printf '  %-18s %s\n' "lpm (debugfs)" "$(grep -E '^\s*lpm\s*[:=]' /sys/kernel/debug/usb/$UDC/params 2>/dev/null | awk '{print $NF}' || echo n/a)"
    echo "  (state should be 'configured' and current_speed 'full-speed' while the target is on;"
    printf '  %-18s %s\n' "suspended" "$(cat "/sys/class/udc/$UDC/gadget/suspended" 2>/dev/null || echo n/a)"
    echo "   lpm 1 means bcdUSB 2.01 plus a BOS descriptor on a stock kernel; with kernel-patches/0002"
    echo "   at full speed the wire is always 2.00 without BOS; suspended 1 = the host suspended the bus)"
else
    echo "== UDC: not bound"
fi
echo "== hidg devices"
ls -l /dev/hidg* 2>/dev/null || echo "  none"
echo "== bridge"
systemctl is-active hid-bridge 2>/dev/null | sed 's/^/  hid-bridge.service: /'
