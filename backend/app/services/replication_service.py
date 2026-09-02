from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.hal import hal
from backend.app.models.file import StoredFile, FileReplicaStatus
from backend.app.services.audit_service import AuditService
from backend.app.core.logger import logger


class ReplicationService:
    """
    Manages asynchronous and synchronous dual-drive replication,
    database replica status updates, and semi-automated rebuild workflows.
    """

    @staticmethod
    def replicate_file(db: Session, stored_file: StoredFile) -> bool:
        """
        Replicate a file from Primary volume to Replica volume and verify SHA-256.
        Updates database StoredFile.replica_status truthfully.
        """
        rel_path = stored_file.storage_path
        logger.info(f"[Replication] Replicating file {stored_file.filename} ({rel_path})...")

        success = hal.replication.replicate(rel_path, hal.primary_storage, hal.replica_storage)
        now = datetime.now(timezone.utc)

        if success:
            stored_file.replica_status = FileReplicaStatus.SYNCED.value
            stored_file.last_verified_at = now
            db.commit()
            AuditService.log_event(
                db, event_type="REPLICATION_COMPLETED",
                description=f"File {stored_file.filename} successfully replicated and verified on replica drive",
                user_id=stored_file.owner_id, severity="INFO"
            )
            return True
        else:
            stored_file.replica_status = FileReplicaStatus.FAILED.value
            db.commit()
            AuditService.log_event(
                db, event_type="REPLICATION_FAILED",
                description=f"Replication failed or checksum mismatch for {stored_file.filename}",
                user_id=stored_file.owner_id, severity="ERROR"
            )
            return False

    @staticmethod
    def trigger_rebuild(db: Session, user_id: int = None, username: str = None) -> Dict[str, Any]:
        """
        Semi-Automated Replica Rebuild:
        Rebuilds secondary drive from primary drive after administrator replaces failed hardware.
        """
        AuditService.log_event(
            db, event_type="REBUILD_STARTED",
            description="Semi-automated replica volume rebuild initiated by administrator",
            user_id=user_id, username=username, severity="WARNING"
        )

        result = hal.replication.rebuild(hal.primary_storage, hal.replica_storage)
        now = datetime.now(timezone.utc)

        if result.get("success"):
            # Update all files in DB to SYNCED
            db.query(StoredFile).filter(
                StoredFile.replica_status != FileReplicaStatus.DELETE_PENDING.value
            ).update({
                StoredFile.replica_status: FileReplicaStatus.SYNCED.value,
                StoredFile.last_verified_at: now
            })
            db.commit()

            AuditService.log_event(
                db, event_type="REBUILD_COMPLETED",
                description=f"Replica rebuild finished successfully. {result.get('rebuilt_count')} files synced.",
                user_id=user_id, username=username, severity="INFO"
            )
        else:
            AuditService.log_event(
                db, event_type="REBUILD_FAILED",
                description=f"Replica rebuild encountered errors: {result.get('errors')}",
                user_id=user_id, username=username, severity="ERROR"
            )

        return result

    @staticmethod
    def retry_pending_or_failed(db: Session) -> Dict[str, Any]:
        """Retry replicating any files marked pending or failed."""
        files = db.query(StoredFile).filter(
            StoredFile.replica_status.in_([FileReplicaStatus.PENDING.value, FileReplicaStatus.FAILED.value])
        ).all()

        synced_count = 0
        failed_count = 0

        for f in files:
            if ReplicationService.replicate_file(db, f):
                synced_count += 1
            else:
                failed_count += 1

        return {
            "retried": len(files),
            "succeeded": synced_count,
            "failed": failed_count
        }

    @staticmethod
    def get_replication_status(db: Session) -> Dict[str, Any]:
        hal_status = hal.replication.get_status()
        pending_db_count = db.query(StoredFile).filter(
            StoredFile.replica_status == FileReplicaStatus.PENDING.value
        ).count()
        failed_db_count = db.query(StoredFile).filter(
            StoredFile.replica_status == FileReplicaStatus.FAILED.value
        ).count()
        synced_db_count = db.query(StoredFile).filter(
            StoredFile.replica_status == FileReplicaStatus.SYNCED.value
        ).count()

        return {
            "engine_state": hal_status.get("state"),
            "engine": hal_status.get("engine"),
            "last_sync_timestamp": hal_status.get("last_sync_timestamp"),
            "db_stats": {
                "synced_count": synced_db_count,
                "pending_count": pending_db_count,
                "failed_count": failed_db_count
            },
            "failed_files": hal_status.get("failed_files", []),
            "is_simulated": hal_status.get("is_simulated", True)
        }
