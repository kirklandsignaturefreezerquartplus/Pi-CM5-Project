#!/bin/sh
# Remove hid-bridge (keeps /etc/hid-bridge and the dwc2 overlay line unless --purge).
set -eu
if [ "$(id -u)" -ne 0 ]; then echo "run as root" >&2; exit 1; fi
systemctl disable --now hid-bridge.service hid-gadget.service 2>/dev/null || true
rm -f /etc/systemd/system/hid-bridge.service /etc/systemd/system/hid-gadget.service
systemctl daemon-reload
rm -f /usr/local/bin/hid-bridge /etc/modules-load.d/hid-bridge.conf
rm -rf /opt/hid-bridge
if [ "${1:-}" = "--purge" ]; then
    rm -rf /etc/hid-bridge
    for f in /boot/firmware/config.txt /boot/config.txt; do
        [ -f "$f" ] && sed -i '/^# hid-bridge: USB device (gadget) mode/d;/^dtoverlay=dwc2,dr_mode=peripheral$/d' "$f"
    done
    echo "purged configuration; reboot to leave USB device mode"
fi
echo "hid-bridge removed"
