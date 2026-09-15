#!/bin/sh
# Install hid-bridge on a Raspberry Pi CM5 running Raspberry Pi OS (Bookworm or newer).
# Usage: sudo ./install.sh          (idempotent; re-run after pulling updates)
set -eu

PREFIX=/opt/hid-bridge
CONFIG_DIR=/etc/hid-bridge
SRC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ "$(id -u)" -ne 0 ]; then
    echo "run as root: sudo $0" >&2
    exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    echo "python3 >= 3.11 is required (Raspberry Pi OS Bookworm ships 3.11)" >&2
    exit 1
fi

echo "==> installing package to $PREFIX"
mkdir -p "$PREFIX"
rm -rf "$PREFIX/hid_bridge"
cp -r "$SRC_DIR/hid_bridge" "$PREFIX/hid_bridge"
find "$PREFIX/hid_bridge" -name '__pycache__' -type d -prune -exec rm -rf {} +
cp "$SRC_DIR/README.md" "$PREFIX/README.md"
rm -rf "$PREFIX/docs"; cp -r "$SRC_DIR/docs" "$PREFIX/docs"
rm -rf "$PREFIX/tools"; cp -r "$SRC_DIR/tools" "$PREFIX/tools"
rm -rf "$PREFIX/kernel-patches"; cp -r "$SRC_DIR/kernel-patches" "$PREFIX/kernel-patches"
install -m 0755 "$SRC_DIR/bin/hid-bridge" /usr/local/bin/hid-bridge

echo "==> configuration"
mkdir -p "$CONFIG_DIR"
if [ -f "$CONFIG_DIR/config.toml" ]; then
    install -m 0644 "$SRC_DIR/config/config.toml" "$CONFIG_DIR/config.toml.dist"
    echo "    kept existing $CONFIG_DIR/config.toml (new defaults in config.toml.dist)"
else
    install -m 0644 "$SRC_DIR/config/config.toml" "$CONFIG_DIR/config.toml"
    # Give this unit a stable, unique serial like a real keyboard would have.
    SERIAL=$(tr -dc 'A-F0-9' </dev/urandom | head -c 12)
    sed -i "s/^serial = \"\"/serial = \"$SERIAL\"/" "$CONFIG_DIR/config.toml"
    echo "    wrote $CONFIG_DIR/config.toml (serial $SERIAL)"
fi

echo "==> kernel modules"
printf 'dwc2\nlibcomposite\n' > /etc/modules-load.d/hid-bridge.conf

BOOT_CONFIG=""
for candidate in /boot/firmware/config.txt /boot/config.txt; do
    if [ -f "$candidate" ]; then BOOT_CONFIG=$candidate; break; fi
done
if [ -n "$BOOT_CONFIG" ]; then
    if grep -Eq '^[[:space:]]*dtoverlay=dwc2' "$BOOT_CONFIG"; then
        if ! grep -Eq '^[[:space:]]*dtoverlay=dwc2.*dr_mode=peripheral' "$BOOT_CONFIG"; then
            echo "    WARNING: $BOOT_CONFIG has a dtoverlay=dwc2 line without dr_mode=peripheral; edit it by hand"
        else
            echo "    $BOOT_CONFIG already has dtoverlay=dwc2,dr_mode=peripheral"
        fi
    else
        cp "$BOOT_CONFIG" "$BOOT_CONFIG.hid-bridge.bak"
        printf '\n# hid-bridge: USB device (gadget) mode on the CM5 USB 2.0 OTG port\n[all]\ndtoverlay=dwc2,dr_mode=peripheral\n' >> "$BOOT_CONFIG"
        echo "    added dtoverlay=dwc2,dr_mode=peripheral to $BOOT_CONFIG (backup: $BOOT_CONFIG.hid-bridge.bak)"
        NEED_REBOOT=1
    fi
else
    echo "    WARNING: no config.txt found; add 'dtoverlay=dwc2,dr_mode=peripheral' to your boot config manually"
fi

echo "==> systemd units"
install -m 0644 "$SRC_DIR/systemd/hid-gadget.service" /etc/systemd/system/hid-gadget.service
install -m 0644 "$SRC_DIR/systemd/hid-bridge.service" /etc/systemd/system/hid-bridge.service
systemctl daemon-reload
systemctl enable hid-gadget.service hid-bridge.service >/dev/null

echo "==> validating configuration"
HID_BRIDGE_CONFIG="$CONFIG_DIR/config.toml" /usr/local/bin/hid-bridge check || true

echo
if [ "${NEED_REBOOT:-0}" = 1 ]; then
    echo "Reboot to activate USB device mode:  sudo reboot"
else
    echo "Start now with:  sudo systemctl start hid-gadget hid-bridge"
fi
echo "Then check:      hid-bridge gadget status ; hid-bridge ctl status ; journalctl -u hid-bridge -f"
