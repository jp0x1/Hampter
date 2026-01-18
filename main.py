"""
Hampter Link Orchestrator.
Combines Networking, Protocol, and UI.
"""
import asyncio
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

# Core Modules
from config import cfg
from src.networking.interface_mgr import InterfaceManager
from src.networking.discovery import DiscoveryService
from src.protocol.certificates import CertificateManager
from src.protocol.quic_server import HampterProtocol, build_quic_config
from src.protocol.quic_client import QuicClient
from src.ui.dashboard import Dashboard

# Libs
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from aioquic.asyncio import serve

# Logging Setup
logging.basicConfig(level=logging.INFO)
# Redirect logging to not mess up UI (ideally)
# For MVP, we might want to capture logs and feed to UI, but prompt_toolkit handles this

class HamperLinkApp:
    def __init__(self):
        self.dashboard = Dashboard()
        self.loop = asyncio.new_event_loop()
        self.quic_client = None
        self.peer_info = None
        
    def start(self):
        # 1. Interface Selection
        ifaces = InterfaceManager.scan_interfaces()
        print("\n[+] Available Interfaces:")
        for idx, i in enumerate(ifaces):
            print(f" {idx}. {i['name']} ({i['driver']}) {'[AX210]' if i['is_ax210'] else ''}")
        
        sel = input("\nSelect Interface ID (default 0): ") or "0"
        selected_iface = ifaces[int(sel)]
        
        # 2. Network Config
        ip = input(f"Enter IP for {selected_iface['name']} (e.g. 10.0.0.1): ")
        channel = input("Enter Channel (default 1): ") or "1"
        
        print(f"[+] Configuring {selected_iface['name']}...")
        if not InterfaceManager.configure_adhoc(selected_iface['name'], ip, int(channel)):
            print("[-] Configuration Failed. Check sudo?")
            return

        cfg.interface = selected_iface['name']
        cfg.ip_address = ip
        self.dashboard.update_info(cfg.interface, cfg.ip_address)

        # 3. Certs
        CertificateManager.ensure_certs()
        
        # 4. Asyncio Loop Start
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.async_main())
        except KeyboardInterrupt:
            pass
        finally:
            print("Shutting down...")

    async def async_main(self):
        # Start QUIC Server
        quic_config = build_quic_config(cfg.CERT_PATH, cfg.KEY_PATH)
        
        def on_server_msg(data, peer):
            self.dashboard.add_log(f"PEER", data)
        
        # Hack to inject callback
        HampterProtocol._on_message_callback = on_server_msg

        server = await serve(
            "0.0.0.0", cfg.DEFAULT_PORT,
            configuration=quic_config,
            create_protocol=HampterProtocol,
        )
        
        # Start Discovery
        discovery = DiscoveryService(self.on_peer_found)
        await discovery.start()
        
        # Start UI & Input Loop
        # We run the Live UI layout refresh task
        ui_task = asyncio.create_task(self.ui_loop())
        
        # Input Loop (PromptToolkit)
        with patch_stdout():
            session = PromptSession()
            while True:
                try:
                    # Non-blocking prompt (async)
                    msg = await session.prompt_async(f"[{cfg.get_hostname()}] > ")
                    if msg.strip():
                        await self.handle_input(msg)
                except (EOFError, KeyboardInterrupt):
                    break

        ui_task.cancel()

    def on_peer_found(self, info, ip):
        if self.peer_info and self.peer_info['ip'] == ip:
            return # Already known
            
        self.peer_info = info
        self.peer_info['ip'] = ip
        self.dashboard.update_peer("FOUND", ip, name=info.get('hostname'))
        self.dashboard.add_log("SYSTEM", f"Peer found: {ip}")
        
        # Initiate QUIC Connection
        asyncio.create_task(self.connect_quic(ip))

    async def connect_quic(self, ip):
        client = QuicClient(cfg.CERT_PATH)
        self.quic_client = client
        
        def on_client_msg(data, _):
            self.dashboard.add_log("PEER", data)
            
        self.dashboard.add_log("SYSTEM", f"Connecting to {ip}...")
        
        # Connect
        await client.connect_to(ip, cfg.DEFAULT_PORT, on_client_msg)
        
        if client.connected:
            self.dashboard.update_peer("CONNECTED", ip, name=self.peer_info.get('hostname'))
            self.dashboard.add_log("SYSTEM", "QUIC Link Established!")

    async def handle_input(self, msg):
        self.dashboard.add_log("ME", msg)
        if self.quic_client and self.quic_client.connected:
            self.quic_client.send_message(msg)
        else:
            self.dashboard.add_log("SYSTEM", "Not connected to peer.")

    async def ui_loop(self):
        """Refreshes the Rich dashboard."""
        with self.dashboard.get_live() as live:
            while True:
                live.update(self.dashboard.generate_layout())
                await asyncio.sleep(0.1)

if __name__ == "__main__":
    app = HamperLinkApp()
    app.start()
