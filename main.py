"""
Hampter Link - Main Entry Point
Supports GUI and CLI modes.
"""
import warnings
warnings.filterwarnings("ignore")

import sys
import asyncio
import argparse
import logging
import json
import signal

# Configure global logging
# Show INFO logs to stdout so we can see Fan debug info in the console mix
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("Main")
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

shutdown_event = asyncio.Event()

def signal_handler(sig, frame):
    shutdown_event.set()

def load_config(path: str = "config.json") -> dict:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "node_type": "A",
            "network": {"interface": "wlan0"},
            "hardware": {"lcd_address": 0x27, "fan_pin": 2},
            "security": {}
        }

async def async_main(args, config):
    from src.hardware.fan_ctrl import fan_ctrl
    from src.hardware.telemetry import Telemetry
    
    lcd = None
    if not args.no_lcd:
        from src.hardware.lcd_drv import LCDDriver
        lcd = LCDDriver(address=config['hardware'].get('lcd_address', 0x27))

    wifi = None
    if not args.no_wifi:
        from src.hardware.wifi_monitor import WifiMonitor
        wifi = WifiMonitor(interface=config['network'].get('interface', 'wlan0'))

    tasks = []
    if not args.no_fan:
        tasks.append(asyncio.create_task(fan_ctrl.start_loop()))
    if lcd:
        tasks.append(asyncio.create_task(lcd.start_scroller()))

    if args.mode == 'cli':
        from src.cli.console import SotaConsole
        console = SotaConsole()
        
        console.set_status_provider(lambda: {
            **Telemetry.get_status_dict(),
            **(wifi.get_stats() if wifi else {})
        })
        
        console.set_fan_handler(lambda s: fan_ctrl.set_manual_speed(s) if s >= 0 else fan_ctrl.set_auto_mode())
        
        console_task = asyncio.create_task(console.run())
        
        await asyncio.wait(
            [asyncio.create_task(shutdown_event.wait()), console_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        console.stop()
    else:
        print("GUI mode requires local display.")
        return

    fan_ctrl.stop()
    if lcd: lcd.stop()
    
    for t in tasks: t.cancel()
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception: pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cli', action='store_true')
    parser.add_argument('--mode', choices=['gui','cli'], default='gui')
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--no-lcd', action='store_true')
    parser.add_argument('--no-fan', action='store_true')
    parser.add_argument('--no-wifi', action='store_true')
    # Add debug flag to enable verbose logging
    parser.add_argument('--debug', action='store_true', help="Enable verbose debug logs")
    args = parser.parse_args()

    if args.cli: args.mode = 'cli'
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("FanCtrl").setLevel(logging.DEBUG)

    config = load_config(args.config)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.mode == 'gui':
        print("Use --cli for console.")
    else:
        try:
            asyncio.run(async_main(args, config))
        except KeyboardInterrupt: pass

if __name__ == "__main__":
    main()
