import hashlib
import os
import re
import uuid
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from backend.app.models.file import StoredFile, FileReplicaStatus
from backend.app.models.user import User, UserRole
from backend.app.hal import hal
from backend.app.services.storage_manager import StorageManager
from backend.app.services.replication_service import ReplicationService
from backend.app.services.audit_service import AuditService
from backend.app.core.exceptions import (
    StorageUnavailableException,
    IntegrityVerificationException,
    FileNotFoundException,
    AuthorizationException
)
from backend.app.core.logger import logger


class FileService:

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal and shell injection."""
        base = os.path.basename(filename)
        sanitized = re.sub(r"[^\w\.-]", "_", base)
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
        1. Validate filename and size
        2. Generate SHA-256 checksum
        3. Write to primary storage provider
        4. Create database metadata record with replica_status='pending'
        5. Trigger replication to replica volume
        6. Return truthful response
        """
        if not hal.encryption.is_unlocked():
            raise StorageUnavailableException("Storage vault is locked. Unlock using Key-SD before uploading.")

        if not hal.primary_storage.is_available():
            raise StorageUnavailableException("Primary storage drive is unavailable or unmounted")

        safe_name = FileService.sanitize_filename(filename)
        file_size = len(data)
        sha256_hash = hashlib.sha256(data).hexdigest()

        # Generate unique storage path on volume to avoid collisions
        unique_id = str(uuid.uuid4())
        storage_rel_path = f"files/{current_user.id}/{unique_id[:8]}_{safe_name}"

        # Write to primary
        hal.primary_storage.write(storage_rel_path, data)

        # Create DB record
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
    def get_file(db: Session, file_id: str, current_user: User) -> StoredFile:
        file_record = db.query(StoredFile).filter(StoredFile.id == file_id).first()
        if not file_record:
            raise FileNotFoundException(f"File {file_id} not found")

        # RBAC: users can only see their own files unless admin
        if current_user.role != UserRole.ADMIN.value and file_record.owner_id != current_user.id:
            raise AuthorizationException("Access denied to requested file")

        return file_record

    @staticmethod
    def download_file(db: Session, file_id: str, current_user: User) -> Tuple[bytes, StoredFile, bool]:
        """
        Download Workflow:
        1. Resolve metadata and access permissions
        2. Determine healthy storage source (Primary or failover to Replica)
        3. Read data
        4. Verify SHA-256 against stored checksum
        5. Return data, record, and whether served in degraded failover mode
        """
        if not hal.encryption.is_unlocked():
            raise StorageUnavailableException("Storage vault is locked. Unlock using Key-SD before downloading.")

        stored_file = FileService.get_file(db, file_id, current_user)

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
    def delete_file(db: Session, file_id: str, current_user: User) -> Dict[str, Any]:
        """
        Careful Delete Workflow:
        Attempts deletion on both primary and replica.
        Handles partial failures truthfully without silently claiming complete deletion.
        """
        stored_file = FileService.get_file(db, file_id, current_user)
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
        if current_user.role != UserRole.ADMIN.value:
            query = query.filter(StoredFile.owner_id == current_user.id)

        if search:
            query = query.filter(StoredFile.filename.ilike(f"%{search}%"))

        if replica_status:
            query = query.filter(StoredFile.replica_status == replica_status)

        files = query.order_by(StoredFile.created_at.desc()).all()
        return [f.to_dict() for f in files]
