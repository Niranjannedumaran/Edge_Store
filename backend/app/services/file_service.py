import hashlib
import os
import re
import uuid
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from backend.app.models.file import StoredFile, FileReplicaStatus
from backend.app.models.user import User, UserRole
from backend.app.models.share import FileShare
from backend.app.hal import hal
from backend.app.services.storage_manager import StorageManager
from backend.app.services.replication_service import ReplicationService
from backend.app.services.audit_service import AuditService
from backend.app.core.exceptions import (
    StorageUnavailableException,
    IntegrityVerificationException,
    FileNotFoundException,
    AuthorizationException,
    SecurityViolationException,
    ValidationException
)
from backend.app.config import settings
from backend.app.core.logger import logger

DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".vbs", ".ps1", ".com", ".scr", ".pif", ".hta", ".cpl"
}


class FileService:

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to strictly prevent path traversal and directory escape.
        Extracts base name, neutralizes traversal tokens, removes null bytes and control chars.
        """
        if not filename or not filename.strip():
            return "unnamed_file"

        # Neutralize null bytes and encoded traversal
        cleaned = filename.replace("\x00", "").replace("%00", "").strip()
        # Extract base name to strip directory traversal (../../)
        base = os.path.basename(cleaned)
        # Neutralize any remaining traversal tokens
        base = base.replace("..", "_").replace("/", "_").replace("\\", "_")
        # Allow only safe alphanumeric and standard filename characters
        sanitized = re.sub(r"[^\w\.-]", "_", base)
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        return sanitized or "unnamed_file"

    @staticmethod
    def upload_file(
        db: Session,
        current_user: User,
        filename: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """
        Complete File Upload Workflow:
        1. Validate filename, size, and extension security
        2. Generate SHA-256 checksum
        3. Write to primary storage provider using atomic write
        4. Create database metadata record with replica_status='pending'
        5. Trigger replication to replica volume with SHA-256 verification
        6. Return truthful response
        """
        if not hal.encryption.is_unlocked():
            raise StorageUnavailableException("Storage vault is locked. Unlock using Key-SD before uploading.")

        if not hal.primary_storage.is_available():
            raise StorageUnavailableException("Primary storage drive is unavailable or unmounted")

        safe_name = FileService.sanitize_filename(filename)

        # Extension and executable upload prevention
        ext = os.path.splitext(safe_name)[1].lower()
        if ext in DANGEROUS_EXTENSIONS:
            AuditService.log_event(
                db, event_type="SECURITY_EVENT",
                description=f"User '{current_user.username}' attempted to upload prohibited executable extension '{ext}' ({safe_name})",
                user_id=current_user.id, username=current_user.username, severity="WARNING"
            )
            raise ValidationException(f"Upload rejected: Disallowed executable file extension '{ext}'")

        file_size = len(data)
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValidationException(f"File size ({file_size} bytes) exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes")

        sha256_hash = hashlib.sha256(data).hexdigest()

        # Generate safe internal UUID storage path on volume to prevent any path injection
        unique_id = str(uuid.uuid4())
        storage_rel_path = f"files/{current_user.id}/{unique_id}"

        # Write to primary with atomic write
        hal.primary_storage.write(storage_rel_path, data)

        # Create DB record (original safe filename preserved in metadata)
        stored_file = StoredFile(
            id=unique_id,
            owner_id=current_user.id,
            filename=safe_name,
            file_size=file_size,
            sha256_hash=sha256_hash,
            storage_path=storage_rel_path,
            content_type=content_type or "application/octet-stream",
            replica_status=FileReplicaStatus.PENDING.value
        )
        db.add(stored_file)
        db.commit()
        db.refresh(stored_file)

        AuditService.log_event(
            db, event_type="FILE_UPLOAD",
            description=f"File {safe_name} ({file_size} bytes) uploaded to primary storage. SHA-256: {sha256_hash[:16]}...",
            user_id=current_user.id, username=current_user.username, severity="INFO"
        )

        # Synchronous replication attempt
        replica_success = ReplicationService.replicate_file(db, stored_file)

        return {
            "file": stored_file.to_dict(),
            "primary_write": True,
            "replica_synced": replica_success,
            "replica_status": stored_file.replica_status,
            "is_degraded": not replica_success
        }

    @staticmethod
    def get_file(db: Session, file_id: str, current_user: User, share_token: Optional[str] = None) -> StoredFile:
        file_record = db.query(StoredFile).filter(StoredFile.id == file_id).first()
        if not file_record:
            raise FileNotFoundException(f"File {file_id} not found")

        # Object-Level Authorization:
        # Permitted if:
        # 1. User is the resource owner
        # 2. User is Super Admin, Storage Admin, or possesses files.manage
        # 3. Request is accompanied by a valid temporary FileShare token
        # 4. User is an active Guest reviewer viewing authorized verified files
        is_owner = (file_record.owner_id == current_user.id)
        is_admin = current_user.role in ("super_admin", "admin", "storage_admin") or current_user.has_permission("files.manage")
        
        has_valid_share = False
        if share_token:
            share = db.query(FileShare).filter(FileShare.id == share_token, FileShare.file_id == file_id).first()
            if share and share.is_valid():
                has_valid_share = True
            else:
                AuditService.log_event(
                    db, event_type="ACCESS_DENIED",
                    description=f"Attempted access with invalid, expired, or revoked share token '{share_token[:8]}...'",
                    severity="WARNING"
                )
                raise AuthorizationException("Share link is invalid, expired, or has reached its usage limit")

        is_guest_viewer = (current_user.role == "guest" and current_user.has_permission("files.preview"))

        if not (is_owner or is_admin or has_valid_share or is_guest_viewer):
            AuditService.log_event(
                db, event_type="ACCESS_DENIED",
                description=f"User '{current_user.username}' (id={current_user.id}) denied access to file '{file_record.filename}' owned by user {file_record.owner_id} (IDOR Defense)",
                user_id=current_user.id, username=current_user.username, severity="WARNING"
            )
            raise AuthorizationException("You do not have permission to access or modify this resource (ownership required)")

        return file_record

    @staticmethod
    def download_file(
        db: Session,
        file_id: str,
        current_user: User,
        share_token: Optional[str] = None
    ) -> Tuple[bytes, StoredFile, bool]:
        """
        Download Workflow:
        1. Resolve metadata and object-level permissions
        2. Determine healthy storage source (Primary or failover to Replica)
        3. Read data
        4. Verify SHA-256 against stored checksum
        5. Return data, record, and whether served in degraded failover mode
        """
        if not hal.encryption.is_unlocked():
            raise StorageUnavailableException("Storage vault is locked. Unlock using Key-SD before downloading.")

        stored_file = FileService.get_file(db, file_id, current_user, share_token=share_token)

        # Check download authorization for share tokens
        if share_token:
            share = db.query(FileShare).filter(FileShare.id == share_token).first()
            if share and not share.allow_download and not current_user.has_permission("files.download"):
                raise AuthorizationException("This share link grants read-only preview. Downloading file is restricted.")

        # Resolve provider with automatic replica failover
        provider, drive_label, is_degraded_fallback = StorageManager.resolve_read_provider(stored_file.storage_path)

        data = provider.read(stored_file.storage_path)

        # Verify integrity
        computed_hash = hashlib.sha256(data).hexdigest()
        if computed_hash.lower() != stored_file.sha256_hash.lower():
            AuditService.log_event(
                db, event_type="INTEGRITY_ALERT",
                description=f"Checksum mismatch reading {stored_file.filename} from {drive_label}! Expected {stored_file.sha256_hash}, got {computed_hash}",
                user_id=current_user.id, username=current_user.username, severity="CRITICAL"
            )
            raise IntegrityVerificationException(f"Integrity check failed reading from {drive_label}")

        AuditService.log_event(
            db, event_type="FILE_DOWNLOAD",
            description=f"File {stored_file.filename} downloaded from {drive_label} (degraded={is_degraded_fallback})",
            user_id=current_user.id, username=current_user.username, severity="INFO"
        )

        return data, stored_file, is_degraded_fallback

    @staticmethod
    def rename_file(db: Session, file_id: str, new_filename: str, current_user: User) -> Dict[str, Any]:
        """Rename an existing file metadata record with IDOR protection."""
        stored_file = FileService.get_file(db, file_id, current_user)

        # IDOR Object-Level Authorization: verify ownership unless administrator
        is_admin = current_user.role in ["super_admin", "storage_admin"] or current_user.has_permission("files.manage")
        if stored_file.owner_id != current_user.id and not is_admin:
            AuditService.log_event(
                db, event_type="ACCESS_DENIED",
                description=f"User '{current_user.username}' attempted unauthorized rename of file '{stored_file.filename}' owned by user {stored_file.owner_id}",
                user_id=current_user.id, username=current_user.username, severity="WARNING"
            )
            raise AuthorizationException("You do not have permission to modify this resource (ownership required)")

        safe_new_name = FileService.sanitize_filename(new_filename)
        old_name = stored_file.filename

        stored_file.filename = safe_new_name
        db.commit()

        AuditService.log_event(
            db, event_type="FILE_RENAME",
            description=f"User '{current_user.username}' renamed file '{old_name}' to '{safe_new_name}'",
            user_id=current_user.id, username=current_user.username, severity="INFO"
        )

        return {
            "success": True,
            "message": f"File renamed to {safe_new_name}",
            "file": stored_file.to_dict()
        }

    @staticmethod
    def delete_file(db: Session, file_id: str, current_user: User) -> Dict[str, Any]:
        """
        Careful Delete Workflow with IDOR protection:
        Attempts deletion on both primary and replica.
        Handles partial failures truthfully without silently claiming complete deletion.
        """
        stored_file = FileService.get_file(db, file_id, current_user)

        # IDOR Object-Level Authorization: verify ownership unless administrator
        is_admin = current_user.role in ["super_admin", "storage_admin"] or current_user.has_permission("files.manage")
        if stored_file.owner_id != current_user.id and not is_admin:
            AuditService.log_event(
                db, event_type="ACCESS_DENIED",
                description=f"User '{current_user.username}' attempted unauthorized deletion of file '{stored_file.filename}' owned by user {stored_file.owner_id}",
                user_id=current_user.id, username=current_user.username, severity="WARNING"
            )
            raise AuthorizationException("You do not have permission to delete this resource (ownership required)")

        rel_path = stored_file.storage_path

        primary_deleted = False
        replica_deleted = False

        if hal.primary_storage.is_available():
            primary_deleted = hal.primary_storage.delete(rel_path)

        if hal.replica_storage.is_available():
            replica_deleted = hal.replica_storage.delete(rel_path)

        # If both deleted or missing on disk, delete DB record
        if primary_deleted and replica_deleted:
            db.delete(stored_file)
            db.commit()
            AuditService.log_event(
                db, event_type="FILE_DELETE",
                description=f"File {stored_file.filename} deleted cleanly from both primary and replica storage",
                user_id=current_user.id, username=current_user.username, severity="INFO"
            )
            return {
                "success": True,
                "status": "COMPLETED",
                "message": "File deleted cleanly from all volumes"
            }
        elif primary_deleted or replica_deleted:
            # Partial failure
            stored_file.replica_status = FileReplicaStatus.DELETE_PENDING.value
            db.commit()
            AuditService.log_event(
                db, event_type="FILE_DELETE_PARTIAL",
                description=f"Partial deletion failure for {stored_file.filename}: primary={primary_deleted}, replica={replica_deleted}",
                user_id=current_user.id, username=current_user.username, severity="WARNING"
            )
            return {
                "success": False,
                "status": "DELETE_PENDING",
                "message": "Partial deletion: drive was unavailable, scheduled for reconciliation",
                "primary_deleted": primary_deleted,
                "replica_deleted": replica_deleted
            }
        else:
            raise StorageUnavailableException("Could not delete file: Storage volumes unavailable")

    @staticmethod
    def verify_file_integrity(db: Session, file_id: str, current_user: User) -> Dict[str, Any]:
        """Explicitly re-checks SHA-256 on primary and replica."""
        stored_file = FileService.get_file(db, file_id, current_user)
        rel_path = stored_file.storage_path

        primary_ok = hal.primary_storage.is_available() and hal.primary_storage.exists(rel_path)
        primary_hash = None
        if primary_ok:
            data_p = hal.primary_storage.read(rel_path)
            primary_hash = hashlib.sha256(data_p).hexdigest()

        replica_ok = hal.replica_storage.is_available() and hal.replica_storage.exists(rel_path)
        replica_hash = None
        if replica_ok:
            data_r = hal.replica_storage.read(rel_path)
            replica_hash = hashlib.sha256(data_r).hexdigest()

        primary_match = (primary_hash == stored_file.sha256_hash) if primary_hash else False
        replica_match = (replica_hash == stored_file.sha256_hash) if replica_hash else False

        return {
            "file_id": stored_file.id,
            "filename": stored_file.filename,
            "expected_hash": stored_file.sha256_hash,
            "primary": {
                "available": primary_ok,
                "hash": primary_hash,
                "intact": primary_match
            },
            "replica": {
                "available": replica_ok,
                "hash": replica_hash,
                "intact": replica_match
            },
            "overall_healthy": (primary_match and replica_match)
        }

    @staticmethod
    def list_files(
        db: Session,
        current_user: User,
        search: Optional[str] = None,
        replica_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = db.query(StoredFile)

        # Resource-Level Scoping:
        # Administrators and guest reviewers view appliance catalog; regular users view their own files.
        is_admin = current_user.role in ("super_admin", "admin", "storage_admin") or current_user.has_permission("files.manage")
        is_guest = (current_user.role == "guest")
        if not is_admin and not is_guest:
            query = query.filter(StoredFile.owner_id == current_user.id)

        if search:
            query = query.filter(StoredFile.filename.ilike(f"%{search}%"))

        if replica_status:
            query = query.filter(StoredFile.replica_status == replica_status)

        files = query.order_by(StoredFile.created_at.desc()).all()
        return [f.to_dict() for f in files]
