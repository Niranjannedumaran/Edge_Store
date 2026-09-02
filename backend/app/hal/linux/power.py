from pathlib import Path
from typing import Dict, Any
from backend.app.hal.interfaces import PowerProvider
from backend.app.config import PowerMode, settings
from backend.app.core.logger import logger


class LinuxPowerProvider(PowerProvider):
    """
    Real Linux Power & Battery Provider.
    Interfaces with Linux sysfs power supply subsystem (/sys/class/power_supply/)
    or attached I2C UPS hat telemetry.
    """

    def __init__(self, battery_sysfs_path: str = "/sys/class/power_supply/BAT0"):
        self.battery_path = Path(battery_sysfs_path)

    def get_battery_level(self) -> int:
        capacity_file = self.battery_path / "capacity"
        if capacity_file.exists():
            try:
                with open(capacity_file, "r") as f:
                    return int(f.read().strip())
            except Exception as e:
                logger.error(f"Error reading battery capacity: {e}")
        # Default fallback if mains powered without battery
        return 100

    def is_charging(self) -> bool:
        status_file = self.battery_path / "status"
        if status_file.exists():
            try:
                with open(status_file, "r") as f:
                    return f.read().strip().lower() in ("charging", "full")
            except Exception:
                pass
        return True

    def get_power_mode(self) -> PowerMode:
        lvl = self.get_battery_level()
        if lvl <= settings.BATTERY_CRITICAL_THRESHOLD:
            return PowerMode.CRITICAL
        elif lvl <= settings.BATTERY_CONSERVATION_THRESHOLD:
            return PowerMode.CONSERVATION
        return PowerMode.NORMAL

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "battery_percent": self.get_battery_level(),
            "is_charging": self.is_charging(),
            "power_mode": self.get_power_mode().value,
            "sysfs_path": str(self.battery_path),
            "is_simulated": False
        }
