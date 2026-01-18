"""
Configuration Management for Hampter Link.
"""
import socket
import os
import json

class Config:
    # Network Defaults
    DEFAULT_PORT = 4433
    DISCOVERY_PORT = 5566
    BEACON_INTERVAL = 2.0  # Seconds
    BEACON_MAGIC = b"HAMPTER_BEACON"
    
    # Paths
    CERT_DIR = "src/certs"
    CERT_PATH = os.path.join(CERT_DIR, "cert.pem")
    KEY_PATH = os.path.join(CERT_DIR, "key.pem")
    
    # UI Theme
    THEME_COLOR_PRIMARY = "cyan"
    THEME_COLOR_SECONDARY = "magenta"
    
    def __init__(self):
        self.interface = None
        self.ip_address = None
        
    @staticmethod
    def get_hostname():
        return socket.gethostname()

    def load_state(self):
        # Could load from a json file if needed
        pass

# Global instance
cfg = Config()
