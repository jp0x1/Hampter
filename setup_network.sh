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

echo "[*] Bringing down $IFACE..."
ip link set "$IFACE" down

echo "[*] Setting ad-hoc (IBSS) mode on channel $CHANNEL..."
iw dev "$IFACE" set type ibss
# Note: For some cards, you might need to leave the type managed and join ibss 
# iw dev "$IFACE" ibss join "hampter-mesh" 2412

echo "[*] Configuring static IP $IP_ADDR..."
ip addr flush dev "$IFACE"
ip addr add "$IP_ADDR/24" dev "$IFACE"

echo "[*] Bringing up $IFACE..."
ip link set "$IFACE" up

# Join the mesh/ibss network
iw dev "$IFACE" ibss join "hampter-net" 2412 

echo "[SUCCESS] $IFACE is ready on $IP_ADDR (Ch $CHANNEL)"
