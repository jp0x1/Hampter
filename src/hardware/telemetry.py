"""
Telemetry Module for Hampter Link.
Gather system statistics (CPU, RAM, Temp, etc).
"""
import psutil
import logging

logger = logging.getLogger("Telemetry")

class Telemetry:
    @staticmethod
    def get_status_dict():
        """Get system status as a dictionary."""
        stats = {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "ram_percent": psutil.virtual_memory().percent,
            "battery": 100
        }
        
        # Disk usage
        try:
            stats["disk_percent"] = psutil.disk_usage('/').percent
        except Exception:
            pass

        # Battery
        if hasattr(psutil, "sensors_battery"):
            batt = psutil.sensors_battery()
            if batt:
                stats["battery"] = int(batt.percent)
        
        # Temperature (Safe Check)
        stats["temp"] = 0.0
        if hasattr(psutil, "sensors_temperatures"):
            try:
                temps = psutil.sensors_temperatures()
                for name in ['cpu_thermal', 'coretemp', 'k10temp', 'acpitz']:
                    if name in temps and temps[name]:
                        stats["temp"] = temps[name][0].current
                        break
                else:
                    # Fallback
                    for entries in temps.values():
                        if entries:
                            stats["temp"] = entries[0].current
                            break
            except Exception as e:
                # Log usage error only once per run usually, but here we just suppress to debug
                logger.debug(f"Temp read failed: {e}")
        
        return stats
