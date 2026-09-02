from typing import Dict, Any, Tuple
from backend.app.hal import hal
from backend.app.hal.interfaces import StorageProvider
from backend.app.core.exceptions import StorageUnavailableException
from backend.app.core.logger import logger


class StorageManager:
    """
    High-level Storage Coordinator.
    Oversees Drive A and Drive B availability, calculates failover routes,
    and reports consolidated volume metrics.
    """

    @staticmethod
    def get_storage_mode() -> str:
        primary_ok = hal.primary_storage.is_available()
        replica_ok = hal.replica_storage.is_available()

        if primary_ok and replica_ok:
            return "NORMAL"
        elif primary_ok or replica_ok:
            return "DEGRADED"
        else:
            return "OFFLINE"

    @staticmethod
    def resolve_read_provider(relative_path: str) -> Tuple[StorageProvider, str, bool]:
        """
        Determines the optimal storage provider for reading a file.
        Returns: (provider, drive_label, is_degraded_fallback)
        """
        primary_ok = hal.primary_storage.is_available()
        replica_ok = hal.replica_storage.is_available()

        if primary_ok and hal.primary_storage.exists(relative_path):
            return hal.primary_storage, "Drive A (Primary)", False

        if replica_ok and hal.replica_storage.exists(relative_path):
            logger.warning(f"Storage Failover: Reading {relative_path} from Drive B (Replica) because Primary is unavailable or missing file")
            return hal.replica_storage, "Drive B (Replica)", True

        # If primary is ok but file wasn't found, check if it exists at all
        if primary_ok:
            raise FileNotFoundError(f"File {relative_path} not found on storage")

        if replica_ok:
            raise FileNotFoundError(f"File {relative_path} not found on replica storage")

        raise StorageUnavailableException("Cannot read file: Both primary and replica storage are unavailable")

    @staticmethod
    def get_storage_overview() -> Dict[str, Any]:
        primary_status = hal.primary_storage.get_status()
        replica_status = hal.replica_storage.get_status()
        mode = StorageManager.get_storage_mode()

        return {
            "mode": mode,
            "primary": primary_status,
            "replica": replica_status,
            "redundancy_active": (mode == "NORMAL"),
            "is_simulated": primary_status.get("is_simulated", True)
        }
