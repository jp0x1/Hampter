#!/bin/bash
# setup_network.sh - Ad-Hoc Network Setup Helper
# Usage: sudo ./setup_network.sh <interface> <ip_address> <channel>

IFACE=$1
IP_ADDR=$2
CHANNEL=${3:-1} # Default to channel 1

if [ -z "$IFACE" ] || [ -z "$IP_ADDR" ]; then
    echo "Usage: sudo ./setup_network.sh <interface> <ip_address> [channel]"
    exit 1
fi

echo "[*] Ensuring clean state for $IFACE..."
# Stop interfering services
echo "[*] Stopping NetworkManager and wpa_supplicant..."
systemctl stop NetworkManager
systemctl stop wpa_supplicant

echo "[*] Bringing down $IFACE..."
ip link set "$IFACE" down

echo "[*] Setting ad-hoc (IBSS) mode on channel $CHANNEL..."
# Try to set type ibss directly
if ! iw dev "$IFACE" set type ibss; then
    echo "[-] Failed to set type IBSS. Attempting to leave managed mode first..."
    # Some drivers need to leave a mesh/network before switching type
    iw dev "$IFACE" disconnect 2>/dev/null
fi

echo "[*] Configuring static IP $IP_ADDR..."
ip addr flush dev "$IFACE"
ip addr add "$IP_ADDR/24" dev "$IFACE"

echo "[*] Bringing up $IFACE..."
ip link set "$IFACE" up

# Join the mesh/ibss network explicitly
# Fixed frequency for 2.4GHz: 2412 + (Channel-1)*5
FREQ=$((2412 + (CHANNEL-1)*5))
echo "[*] Joining IBSS network 'hampter-net' on $FREQ MHz..."
iw dev "$IFACE" ibss join "hampter-net" $FREQ

echo "[SUCCESS] $IFACE is ready on $IP_ADDR (Ch $CHANNEL)"
