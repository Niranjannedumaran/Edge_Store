from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.hal import hal
from backend.app.config import settings, PowerMode
from backend.app.services.storage_manager import StorageManager
from backend.app.services.replication_service import ReplicationService


class HealthService:
    """
    Consolidated System Health and Telemetry Service.
    Integrates all HAL providers to deliver real-time system state.
    """

    @staticmethod
    def get_system_health(db: Session) -> Dict[str, Any]:
        storage_overview = StorageManager.get_storage_overview()
        vault_unlocked = hal.encryption.is_unlocked()
        key_status = hal.key_device.get_status()
        replication_status = ReplicationService.get_replication_status(db)
        power_telemetry = hal.power.get_telemetry()
        system_metrics = hal.monitor.get_metrics()

        # Compute high-level operational status
        if not vault_unlocked:
            status = "LOCKED"
        elif storage_overview["mode"] == "OFFLINE" or power_telemetry["power_mode"] == PowerMode.CRITICAL.value:
            status = "CRITICAL"
        elif storage_overview["mode"] == "DEGRADED" or replication_status["engine_state"] in ("failed", "degraded"):
            status = "DEGRADED"
        else:
            status = "HEALTHY"

        return {
            "overall_status": status,
            "environment_mode": settings.ENVIRONMENT_MODE.value,
            "is_simulated": storage_overview["is_simulated"],
            "storage": storage_overview,
            "vault": {
                "unlocked": vault_unlocked,
                "encryption": hal.encryption.get_status(),
                "key_sd": key_status
            },
            "replication": replication_status,
            "power": power_telemetry,
            "system_resources": system_metrics
        }
