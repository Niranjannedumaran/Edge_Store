from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.hal import hal
from backend.app.services.audit_service import AuditService
from backend.app.core.exceptions import VaultLockedException, EdgeStoreException
from backend.app.core.logger import logger


class KeyVaultService:
    """
    Manages the Key-SD hardware lifecycle and coordinates safe encryption unlock/lock workflows.
    """

    @staticmethod
    def get_vault_status() -> Dict[str, Any]:
        key_status = hal.key_device.get_status()
        encryption_status = hal.encryption.get_status()
        return {
            "key_sd": key_status,
            "encryption": encryption_status,
            "vault_unlocked": hal.encryption.is_unlocked()
        }

    @staticmethod
    def unlock_vault(db: Session, user_id: int = None, username: str = None) -> Dict[str, Any]:
        """
        Executes safe vault unlock sequence:
        1. Validate Key-SD presence and key material
        2. Attempt LUKS/crypto unlock
        3. Mount primary and replica storage filesystems
        4. Record audit event
        """
        if not hal.key_device.is_present():
            raise VaultLockedException("Cannot unlock vault: Key-SD physical device is missing")

        if not hal.key_device.validate():
            raise VaultLockedException("Cannot unlock vault: Key-SD device signature or keyfile is invalid")

        key_material = hal.key_device.get_key_material()
        if not key_material:
            raise VaultLockedException("Cannot unlock vault: Failed to extract key material from Key-SD")

        unlocked = hal.encryption.unlock(key_material)
        if not unlocked:
            AuditService.log_event(
                db, event_type="VAULT_UNLOCK_FAILED",
                description="Failed attempt to unlock encryption vault with Key-SD",
                user_id=user_id, username=username, severity="ERROR"
            )
            raise VaultLockedException("Failed to unlock storage vault: Invalid cryptographic key token")

        # Mount storage volumes
        mount_a = hal.primary_storage.mount()
        mount_b = hal.replica_storage.mount()

        AuditService.log_event(
            db, event_type="VAULT_UNLOCKED",
            description="Storage vault successfully unlocked and volumes mounted using Key-SD",
            user_id=user_id, username=username, severity="INFO"
        )

        return {
            "success": True,
            "message": "Vault unlocked and storage volumes mounted successfully",
            "primary_mounted": mount_a,
            "replica_mounted": mount_b
        }

    @staticmethod
    def lock_vault(db: Session, user_id: int = None, username: str = None) -> Dict[str, Any]:
        """
        Executes safe vault locking sequence:
        1. Flush pending filesystem writes
        2. Unmount storage volumes safely
        3. Close LUKS / crypto mapper
        4. Record audit event
        """
        logger.warning("[Vault Service] Executing safe vault lock...")

        # Unmount filesystems first to prevent data corruption
        hal.primary_storage.unmount()
        hal.replica_storage.unmount()

        # Lock encryption layer
        locked = hal.encryption.lock()

        AuditService.log_event(
            db, event_type="VAULT_LOCKED",
            description="Storage vault unmounted and locked safely",
            user_id=user_id, username=username, severity="WARNING"
        )

        return {
            "success": locked,
            "message": "Storage vault unmounted and locked safely"
        }
