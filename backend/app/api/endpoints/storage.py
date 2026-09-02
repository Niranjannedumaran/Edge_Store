from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.core.dependencies import get_current_user, require_admin
from backend.app.services.storage_manager import StorageManager
from backend.app.services.key_vault_service import KeyVaultService

router = APIRouter(prefix="/storage", tags=["Storage & Vault"])


@router.get("/status")
def get_storage_status(current_user: User = Depends(get_current_user)):
    overview = StorageManager.get_storage_overview()
    vault = KeyVaultService.get_vault_status()
    return {
        "storage": overview,
        "vault": vault
    }


@router.post("/vault/unlock")
def unlock_vault(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return KeyVaultService.unlock_vault(db, user_id=current_user.id, username=current_user.username)


@router.post("/vault/lock")
def lock_vault(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return KeyVaultService.lock_vault(db, user_id=current_user.id, username=current_user.username)
