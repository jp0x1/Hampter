"""
Fan Controller for Hampter Link.
Provides PWM-based fan speed control based on CPU temperature.
"""
import asyncio
import logging
import sys

# Configure specific logger for Fan
logger = logging.getLogger("FanCtrl")
# DO NOT FORCE LEVEL HERE - let main.py control it via arguments
# logger.setLevel(logging.DEBUG) 

MOCK_GPIO = False

try:
    from gpiozero import PWMOutputDevice, Device
    from gpiozero.exc import BadPinFactory
    
    try:
        factory = Device._default_pin_factory()
        logger.debug(f"GPIO Factory: {factory}")
        Device.ensure_pin_factory()
    except Exception as e:
        logger.warning(f"GPIO Factory check failed: {e}")
        MOCK_GPIO = True
        
except ImportError as e:
    logger.warning(f"GPIOZero import failed: {e}")
    MOCK_GPIO = True

if MOCK_GPIO:
    logger.warning("!!! USING MOCK FAN (GPIO UNAVAILABLE) !!!")
else:
    logger.info("GPIO Loaded Successfully")


class MockPWMDevice:
    """Mock PWM device that logs value changes."""
    def __init__(self, pin: int):
        self.pin = pin
        self._value = 0.0
        logger.debug(f"[Mock] Initialized Fan on Pin {pin}")
    
    @property
    def value(self) -> float:
        return self._value
    
    @value.setter
    def value(self, val: float):
        self._value = val
        logger.debug(f"[Mock] Fan Pin {self.pin} set to {val*100:.1f}%")
    
    def close(self):
        logger.debug(f"[Mock] Fan Pin {self.pin} closed")


# Try to import psutil for temperature reading
try:
    import psutil
except ImportError:
    psutil = None
    logger.warning("psutil unavailable (using mock temp)")


class FanController:
    """
    PWM Fan Controller with debug logging.
    """
    
    FAN_CURVE = [
        (40, 0.0),
        (50, 0.3),
        (60, 0.6),
        (70, 0.8),
        (80, 1.0),
    ]
    
    def __init__(self, pin: int = 2):
        self.pin = pin
        self.running = False
        self._current_speed = 0.0
        self._manual_override = False
        
        logger.info(f"Initializing FanController on Pin {pin}")
        
        if MOCK_GPIO:
            self.fan = MockPWMDevice(pin)
        else:
            try:
                self.fan = PWMOutputDevice(pin, active_high=True, initial_value=0)
                logger.info(f"HARDWARE FAN INITIALIZED on GPIO {pin}")
            except Exception as e:
                logger.error(f"FATAL: Could not create PWMDevice on Pin {pin}: {e}")
                self.fan = MockPWMDevice(pin)

    async def start_loop(self):
        """Start the automatic fan control loop."""
        self.running = True
        logger.info("Fan Control Loop STARTED")
        
        while self.running:
            try:
                if not self._manual_override:
                    temp = self._get_cpu_temp()
                    speed = self._calculate_speed(temp)
                    
                    if abs(speed - self._current_speed) > 0.01:
                        logger.debug(f"AUTO-ADJUST: Temp={temp:.1f}C -> Fan={speed*100:.0f}%")
                        self._apply_speed(speed)
                
            except Exception as e:
                logger.error(f"Loop Error: {e}")
            
            for _ in range(20): 
                if not self.running: break
                await asyncio.sleep(0.1)

    def _apply_speed(self, speed: float):
        try:
            self.fan.value = speed
            self._current_speed = speed
        except Exception as e:
            logger.error(f"Failed to write PWM: {e}")

    def stop(self):
        logger.info("Stopping Fan Controller...")
        self.running = False
        try:
            self.fan.value = 0
            self.fan.close()
        except Exception:
            pass

    def set_manual_speed(self, speed_percent: int):
        logger.info(f"MANUAL OVERRIDE: Setting fan to {speed_percent}%")
        self._manual_override = True
        target = max(0.0, min(1.0, speed_percent / 100))
        self._apply_speed(target)

    def set_auto_mode(self):
        logger.info("Returning to AUTO mode")
        self._manual_override = False

    def _get_cpu_temp(self) -> float:
        """Get cpu temp safely across platforms."""
        if psutil is None: return 45.0
        
        try:
            # Check if sensors_temperatures exists (Linux)
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                for name in ['cpu_thermal', 'coretemp', 'k10temp', 'acpitz']:
                    if name in temps and temps[name]:
                        return temps[name][0].current
                # Fallback to any sensor
                for entries in temps.values():
                    if entries: return entries[0].current
            else:
                # MacOS or Windows fallback (no standard sensor API in psutil)
                return 45.0
                
        except Exception as e:
            logger.error(f"Temp Read Error: {e}")
        
        return 45.0

    def _calculate_speed(self, temp: float) -> float:
        if temp <= self.FAN_CURVE[0][0]: return self.FAN_CURVE[0][1]
        if temp >= self.FAN_CURVE[-1][0]: return self.FAN_CURVE[-1][1]
        
        for i in range(len(self.FAN_CURVE) - 1):
            t1, s1 = self.FAN_CURVE[i]
            t2, s2 = self.FAN_CURVE[i + 1]
            if t1 <= temp < t2:
                ratio = (temp - t1) / (t2 - t1)
                return s1 + ratio * (s2 - s1)
        return 1.0


fan_ctrl = FanController()
