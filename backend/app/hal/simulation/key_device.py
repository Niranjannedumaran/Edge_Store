import os
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.hal.interfaces import KeyDeviceProvider
from backend.app.config import KeySDState
from backend.app.core.logger import logger


class SimulationKeyProvider(KeyDeviceProvider):
    """
    Simulation KeyDevice Provider for removable physical Key-SD.
    Reads key material from the simulated Key-SD volume path.
    Supports developer controls to simulate removal, insertion, and invalid key scenarios.
    """

    def __init__(self, key_sd_path: str, key_file_name: str = "vault.key"):
        self.key_sd_path = Path(key_sd_path).resolve()
        self.key_file_name = key_file_name
        self._state: KeySDState = KeySDState.INSERTED
        self._simulated_device_id = "SD-SIM-01-SN48921"
        self._simulated_uuid = "EDGESTORE-KEY-01"

    def is_present(self) -> bool:
        """Present only if not simulated removed and path exists."""
        return self._state != KeySDState.REMOVED and self.key_sd_path.exists()

    def validate(self) -> bool:
        """Validates that Key-SD is present and contains a valid keyfile."""
        if not self.is_present() or self._state == KeySDState.INVALID:
            return False
        keyfile = self.key_sd_path / self.key_file_name
        return keyfile.exists() and keyfile.stat().st_size > 0

    def get_key_material(self) -> Optional[bytes]:
        if not self.validate():
            return None
        keyfile = self.key_sd_path / self.key_file_name
        with open(keyfile, "rb") as f:
            return f.read().strip()

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "present": self.is_present(),
            "valid": self.validate(),
            "device_id": self._simulated_device_id if self.is_present() else None,
            "uuid": self._simulated_uuid if self.is_present() else None,
            "mount_path": str(self.key_sd_path),
            "key_file": self.key_file_name,
            "is_simulated": True,
        }

    # Simulation Fault Injection & Control
    def simulate_remove(self):
        logger.warning("Hardware Simulation: Physical Key-SD REMOVED")
        self._state = KeySDState.REMOVED

    def simulate_insert(self, valid: bool = True):
        logger.info(f"Hardware Simulation: Physical Key-SD INSERTED (valid={valid})")
        self._state = KeySDState.INSERTED if valid else KeySDState.INVALID
