"""
Discovery Module.
Handles UDP Beacon broadcasting and listening.
"""
import asyncio
import socket
import logging
import json
from config import cfg

logger = logging.getLogger("Discovery")

class DiscoveryProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_peer_found_callback):
        self.on_peer_found = on_peer_found_callback
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        # Enable Broadcast
        sock = transport.get_extra_info('socket')
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def datagram_received(self, data, addr):
        # Ignore our own messages (in production we'd filter by sender ID)
        # For now, just decode
        try:
            if data.startswith(cfg.BEACON_MAGIC):
                payload = data[len(cfg.BEACON_MAGIC):]
                info = json.loads(payload)
                # Filter out ourselves (using hostname is a simple way)
                if info.get('hostname') == cfg.get_hostname():
                    return
                
                self.on_peer_found(info, addr[0])
        except Exception:
            pass

class DiscoveryService:
    def __init__(self, on_peer_found):
        self.on_peer_found = on_peer_found
        self.transport = None
        self.protocol = None
        self.broadcasting = False

    async def start(self):
        loop = asyncio.get_running_loop()
        # Bind to 0.0.0.0 to receive broadcast
        self.transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(self.on_peer_found),
            local_addr=('0.0.0.0', cfg.DISCOVERY_PORT),
            allow_broadcast=True
        )
        logger.info(f"Discovery Listener started on port {cfg.DISCOVERY_PORT}")
        
        # Start broadcast loop
        self.broadcasting = True
        asyncio.create_task(self._broadcast_loop())

    async def _broadcast_loop(self):
        while self.broadcasting:
            if self.transport:
                msg = {
                    "hostname": cfg.get_hostname(),
                    "status": "READY"
                }
                payload = cfg.BEACON_MAGIC + json.dumps(msg).encode()
                # Broadcast address
                self.transport.sendto(payload, ('<broadcast>', cfg.DISCOVERY_PORT))
            
            await asyncio.sleep(cfg.BEACON_INTERVAL)

    def stop(self):
        self.broadcasting = False
        if self.transport:
            self.transport.close()
