import subprocess
import time
import psutil
from typing import Dict, Any, Optional
from backend.app.hal.interfaces import SystemMonitorProvider
from backend.app.core.logger import logger


class LinuxSystemMonitorProvider(SystemMonitorProvider):
    """
    Real Linux System Monitor Provider for Raspberry Pi 4.
    Reads vcgencmd for SoC thermal values, psutil for CPU/RAM,
    and Linux /proc/uptime.
    """

    def __init__(self):
        pass

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
        except Exception:
            return {"total_bytes": 0, "used_bytes": 0, "free_bytes": 0, "percent": 0.0}

    def get_temperature(self) -> Optional[float]:
        # Try Raspberry Pi vcgencmd first
        try:
            res = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True, check=False)
            if res.returncode == 0 and "temp=" in res.stdout:
                # Output format: temp=48.2'C
                raw = res.stdout.strip().replace("temp=", "").replace("'C", "")
                return float(raw)
        except Exception:
            pass

        # Try sysfs thermal zone
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                raw_millidegrees = int(f.read().strip())
                return round(raw_millidegrees / 1000.0, 1)
        except Exception:
            pass

        return None

    def get_uptime_seconds(self) -> float:
        try:
            with open("/proc/uptime", "r") as f:
                return float(f.readline().split()[0])
        except Exception:
            return round(time.time() - psutil.boot_time(), 1)

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "cpu_percent": self.get_cpu_percent(),
            "memory": self.get_memory_usage(),
            "temperature_celsius": self.get_temperature(),
            "uptime_seconds": self.get_uptime_seconds(),
            "platform": "Raspberry Pi 4 (Raspberry Pi OS / Linux kernel)",
            "is_simulated": False
        }
