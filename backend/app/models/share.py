import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


class FileShare(Base):
    __tablename__ = "file_shares"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    allow_download = Column(Boolean, default=False, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    max_uses = Column(Integer, nullable=True)
    access_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    file = relationship("StoredFile", backref="shares")
    creator = relationship("User", backref="created_shares")

    def is_valid(self) -> bool:
        if self.is_revoked:
            return False
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > exp:
            return False
        if self.max_uses is not None and self.access_count >= self.max_uses:
            return False
        return True

    def to_dict(self):
        return {
            "id": self.id,
            "file_id": self.file_id,
            "filename": self.file.filename if self.file else "unknown",
            "file_size": self.file.file_size if self.file else 0,
            "created_by_id": self.created_by_id,
            "created_by_username": self.creator.username if self.creator else "unknown",
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "allow_download": self.allow_download,
            "is_revoked": self.is_revoked,
            "max_uses": self.max_uses,
            "access_count": self.access_count,
            "is_valid": self.is_valid(),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
