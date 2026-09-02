from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.core.dependencies import get_current_user, require_permission
from backend.app.services.replication_service import ReplicationService

router = APIRouter(prefix="/replication", tags=["Replication"])


@router.get("/status")
def get_replication_status(
    current_user: User = Depends(require_permission("replication.read")),
    db: Session = Depends(get_db)
):
    return ReplicationService.get_replication_status(db)


@router.post("/sync")
def trigger_retry_sync(
    current_user: User = Depends(require_permission("replication.manage")),
    db: Session = Depends(get_db)
):
    return ReplicationService.retry_pending_or_failed(db)


@router.post("/rebuild")
def trigger_semi_automated_rebuild(
    current_user: User = Depends(require_permission("replication.rebuild")),
    db: Session = Depends(get_db)
):
    return ReplicationService.trigger_rebuild(db, user_id=current_user.id, username=current_user.username)
