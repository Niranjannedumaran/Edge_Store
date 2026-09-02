from typing import Dict, Any
from backend.app.hal.interfaces import EncryptionProvider
from backend.app.config import VaultState
from backend.app.core.logger import logger


class SimulationEncryptionProvider(EncryptionProvider):
    """
    Simulation Encryption Provider.
    Does NOT pretend normal folders are encrypted LUKS volumes.
    Explicitly tracks and models the cryptographic vault state (LOCKED / UNLOCKED),
    ensuring that access to data volumes requires key unlock workflow.
    """

    def __init__(self, expected_token_prefix: str = "EDGESTORE-LUKS2-SIMULATED-KEY"):
        self.expected_token_prefix = expected_token_prefix
        self._state: VaultState = VaultState.UNLOCKED  # Defaults to unlocked on initial simulation setup

    def is_unlocked(self) -> bool:
        return self._state == VaultState.UNLOCKED

    def unlock(self, key_material: bytes) -> bool:
        if not key_material:
            logger.error("Simulation Encryption: Unlock failed, empty key material")
            return False

        try:
            key_str = key_material.decode("utf-8", errors="ignore")
            if self.expected_token_prefix in key_str:
                self._state = VaultState.UNLOCKED
                logger.info("Simulation Encryption: Vault UNLOCKED successfully")
                return True
            else:
                logger.error("Simulation Encryption: Unlock failed, invalid key token")
                return False
        except Exception as e:
            logger.error(f"Simulation Encryption: Unlock exception: {e}")
            return False

    def lock(self) -> bool:
        self._state = VaultState.LOCKED
        logger.warning("Simulation Encryption: Vault LOCKED")
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "unlocked": self.is_unlocked(),
            "cipher": "aes-xts-plain64 (Simulated LUKS2)",
            "keysize": 512,
            "hash": "sha256",
            "is_simulated": True,
            "hardware_notice": "SIMULATED STORAGE — LUKS HARDWARE NOT CONNECTED"
        }
