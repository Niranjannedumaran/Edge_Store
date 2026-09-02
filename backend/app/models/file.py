import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


class FileReplicaStatus(str, Enum):
    SYNCED = "synced"
    PENDING = "pending"
    FAILED = "failed"
    DEGRADED = "degraded"
    DELETE_PENDING = "delete_pending"


class StoredFile(Base):
    __tablename__ = "files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False, index=True)
    file_size = Column(BigInteger, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    storage_path = Column(String(512), nullable=False, unique=True)
    content_type = Column(String(128), default="application/octet-stream")
    replica_status = Column(String(32), default=FileReplicaStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_verified_at = Column(DateTime, nullable=True)

    owner = relationship("User", backref="files")

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "owner_username": self.owner.username if self.owner else "unknown",
            "filename": self.filename,
            "file_size": self.file_size,
            "sha256_hash": self.sha256_hash,
            "storage_path": self.storage_path,
            "content_type": self.content_type,
            "replica_status": self.replica_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
        }
