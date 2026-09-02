import time
import psutil
from typing import Dict, Any, Optional
from backend.app.hal.interfaces import SystemMonitorProvider
from backend.app.core.logger import logger


class SimulationSystemMonitorProvider(SystemMonitorProvider):
    """
    Simulation System Monitor Provider.
    Collects real host CPU and memory telemetry via psutil,
    with realistic simulated Raspberry Pi thermal metrics and uptime.
    """

    def __init__(self):
        self._start_time = time.time()
        self._base_temp: float = 43.5

    def get_cpu_percent(self) -> float:
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0

    def get_memory_usage(self) -> Dict[str, Any]:
        try:
            mem = psutil.virtual_memory()
            return {
                "total_bytes": mem.total,
                "used_bytes": mem.used,
                "free_bytes": mem.available,
                "percent": mem.percent
            }
        except Exception as e:
            logger.error(f"Error fetching memory metrics: {e}")
            return {"total_bytes": 0, "used_bytes": 0, "free_bytes": 0, "percent": 0.0}

    def get_temperature(self) -> Optional[float]:
        # On Windows/simulation laptops without vcgencmd / thermal sensors,
        # provide a realistic Raspberry Pi 4 operating temperature correlated with CPU usage.
        cpu = self.get_cpu_percent()
        fluctuation = (cpu / 100.0) * 8.0  # Max +8°C under full load
        return round(self._base_temp + fluctuation, 1)

    def get_uptime_seconds(self) -> float:
        return round(time.time() - self._start_time, 1)

    def get_metrics(self) -> Dict[str, Any]:
        mem = self.get_memory_usage()
        return {
            "cpu_percent": self.get_cpu_percent(),
            "memory": mem,
            "temperature_celsius": self.get_temperature(),
            "uptime_seconds": self.get_uptime_seconds(),
            "platform": "Simulated Raspberry Pi 4 (ARM Cortex-A72 / Host OS)",
            "is_simulated": True
        }
