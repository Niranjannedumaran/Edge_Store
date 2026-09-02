from typing import Dict, Any
from backend.app.hal.interfaces import PowerProvider
from backend.app.config import PowerMode, settings
from backend.app.core.logger import logger


class SimulationPowerProvider(PowerProvider):
    """
    Simulation Power Provider.
    Models energy telemetry and policy transitions for development/simulation mode.
    Documented policy thresholds are engineering parameters, not arbitrary claims.
    """

    def __init__(self):
        self._battery_level: int = 100
        self._is_charging: bool = True
        self._simulated_voltage: float = 5.12  # Raspberry Pi 5V nominal

    def get_battery_level(self) -> int:
        return self._battery_level

    def is_charging(self) -> bool:
        return self._is_charging

    def get_power_mode(self) -> PowerMode:
        if self._battery_level <= settings.BATTERY_CRITICAL_THRESHOLD:
            return PowerMode.CRITICAL
        elif self._battery_level <= settings.BATTERY_CONSERVATION_THRESHOLD:
            return PowerMode.CONSERVATION
        else:
            return PowerMode.NORMAL

    def get_telemetry(self) -> Dict[str, Any]:
        mode = self.get_power_mode()
        return {
            "battery_percent": self._battery_level,
            "is_charging": self._is_charging,
            "power_mode": mode.value,
            "voltage": self._simulated_voltage,
            "policy": {
                "normal_threshold": settings.BATTERY_NORMAL_THRESHOLD,
                "conservation_threshold": settings.BATTERY_CONSERVATION_THRESHOLD,
                "critical_threshold": settings.BATTERY_CRITICAL_THRESHOLD,
                "description": "Configurable engineering policy parameters"
            },
            "is_simulated": True
        }

    # Simulation Developer Controls
    def set_battery_level(self, level: int):
        clamped = max(0, min(100, level))
        self._battery_level = clamped
        logger.info(f"Hardware Simulation: Set battery level to {clamped}% (Mode: {self.get_power_mode().value})")

    def set_charging(self, charging: bool):
        self._is_charging = charging
        logger.info(f"Hardware Simulation: Set charging state to {charging}")
