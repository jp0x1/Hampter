"""
Interface Management Module.
Handles detection and configuration of network interfaces.
"""
import subprocess
import logging
import re
from typing import List, Dict, Optional
import netifaces

logger = logging.getLogger("InterfaceMgr")

class InterfaceManager:
    @staticmethod
    def scan_interfaces() -> List[Dict[str, str]]:
        """
        Scan for wireless interfaces and return details.
        Returns: List of dicts {'name': str, 'driver': str, 'mac': str, 'is_ax210': bool}
        """
        interfaces = []
        try:
            # Use 'ip link' to get basic list
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                # Basic parsing, in reality we might want 'ethtool -i' for driver info
                # Match: 3: wlan0: <...>
                match = re.search(r'\d+: ([\w\d]+):', line)
                if match:
                    iface = match.group(1)
                    if not iface.startswith('wl'): continue # Skip non-wireless usually
                    
                    details = {
                        'name': iface,
                        'mac': 'Unknown',
                        'driver': 'Unknown',
                        'is_ax210': False
                    }
                    
                    # Get Driver Info
                    try:
                        ethtool = subprocess.run(['ethtool', '-i', iface], capture_output=True, text=True)
                        if "driver: iwlwifi" in ethtool.stdout:
                            details['driver'] = "iwlwifi"
                            # Loose check for AX210 based on driver or lspci if needed
                            # For MVP assume if it's iwlwifi on a Pi, it's likely our PCIe card
                            details['is_ax210'] = True 
                    except FileNotFoundError:
                        pass # ethtool might not be installed

                    interfaces.append(details)
                    
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            # Fallback for dev/mac (netifaces)
            for iface in netifaces.interfaces():
                if iface.startswith('en') or iface.startswith('wl'):
                     interfaces.append({'name': iface, 'driver': 'N/A', 'is_ax210': False})

        return interfaces

    @staticmethod
    def configure_adhoc(interface: str, ip: str, channel: int = 1) -> bool:
        """
        Configure interface for Ad-Hoc (IBSS) mode.
        Requires sudo.
        """
        logger.info(f"Configuring {interface} for Ad-Hoc on Ch{channel} with IP {ip}")
        try:
            # Call the helper script to handle the sudo/os commands
            cmd = ["sudo", "./setup_network.sh", interface, ip, str(channel)]
            subprocess.check_call(cmd)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Configuration failed: {e}")
            return False
