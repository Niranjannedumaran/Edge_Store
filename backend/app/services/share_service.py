import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.share import FileShare
from backend.app.models.file import StoredFile
from backend.app.models.user import User
from backend.app.services.audit_service import AuditService
from backend.app.core.exceptions import (
    FileNotFoundException,
    AuthorizationException,
    ValidationException
)
from backend.app.config import settings
from backend.app.core.logger import logger


class ShareService:
    """
    Manages secure, temporary, revocable guest sharing of specific files.
    Enforces object-level ownership checks, time-based expiration, and usage counters.
    """

    @staticmethod
    def create_share(
        db: Session,
        file_id: str,
        current_user: User,
        expires_in_hours: int = 24,
        allow_download: bool = False,
        max_uses: Optional[int] = None
    ) -> FileShare:
        file_record = db.query(StoredFile).filter(StoredFile.id == file_id).first()
        if not file_record:
            raise FileNotFoundException(f"File {file_id} not found")

        # Object-level authorization: must be owner or administrator
        is_admin = current_user.role in ("super_admin", "admin", "storage_admin") or current_user.has_permission("files.manage")
        if file_record.owner_id != current_user.id and not is_admin:
            AuditService.log_event(
                db, event_type="ACCESS_DENIED",
                description=f"User '{current_user.username}' attempted to share file '{file_record.filename}' owned by user {file_record.owner_id}",
                user_id=current_user.id, username=current_user.username, severity="WARNING"
            )
            raise AuthorizationException("You do not have permission to share this file (ownership required)")

        if expires_in_hours < 1 or expires_in_hours > 720:  # 1 hour to 30 days max
            raise ValidationException("Expiration hours must be between 1 and 720 hours")

        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        share_token = str(uuid.uuid4())

        share = FileShare(
            id=share_token,
            file_id=file_id,
            created_by_id=current_user.id,
            expires_at=expires_at,
            allow_download=allow_download,
            max_uses=max_uses,
            access_count=0,
            is_revoked=False
        )
        db.add(share)
        db.commit()
        db.refresh(share)

        AuditService.log_event(
            db, event_type="SHARE_CREATED",
            description=f"User '{current_user.username}' created temporary share for '{file_record.filename}' (expires: {expires_at.isoformat()}, allow_download={allow_download})",
            user_id=current_user.id, username=current_user.username, severity="INFO"
        )

        return share

    @staticmethod
    def get_valid_share(db: Session, share_token: str) -> FileShare:
        share = db.query(FileShare).filter(FileShare.id == share_token).first()
        if not share or not share.is_valid():
            AuditService.log_event(
                db, event_type="SECURITY_EVENT",
                description=f"Attempted access with invalid, expired, or revoked share token '{share_token[:8]}...'",
                severity="WARNING"
            )
            raise AuthorizationException("Share link is invalid, expired, or has reached its usage limit")

        # Increment access counter
        share.access_count += 1
        db.commit()

        AuditService.log_event(
            db, event_type="SHARE_ACCESSED",
            description=f"Share token '{share.id[:8]}...' accessed for file '{share.file.filename}' (uses: {share.access_count})",
            severity="INFO"
        )

        return share

    @staticmethod
    def revoke_share(db: Session, share_id: str, current_user: User) -> Dict[str, Any]:
        share = db.query(FileShare).filter(FileShare.id == share_id).first()
        if not share:
            raise FileNotFoundException("Share link not found")

        is_admin = current_user.role in ("super_admin", "admin", "security_admin") or current_user.has_permission("files.manage")
        if share.created_by_id != current_user.id and not is_admin:
            raise AuthorizationException("Only the share creator or administrator can revoke this share")

        share.is_revoked = True
        db.commit()

        AuditService.log_event(
            db, event_type="SHARE_REVOKED",
            description=f"User '{current_user.username}' revoked share token '{share.id[:8]}...' for file '{share.file.filename}'",
            user_id=current_user.id, username=current_user.username, severity="WARNING"
        )

        return {"success": True, "message": "Share link revoked successfully"}

    @staticmethod
    def list_shares_for_file(db: Session, file_id: str, current_user: User) -> List[Dict[str, Any]]:
        file_record = db.query(StoredFile).filter(StoredFile.id == file_id).first()
        if not file_record:
            raise FileNotFoundException("File not found")

        is_admin = current_user.role in ("super_admin", "admin", "storage_admin") or current_user.has_permission("files.manage")
        if file_record.owner_id != current_user.id and not is_admin:
            raise AuthorizationException("Access denied to file shares")

        shares = db.query(FileShare).filter(FileShare.file_id == file_id).order_by(FileShare.created_at.desc()).all()
        return [s.to_dict() for s in shares]
