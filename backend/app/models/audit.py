from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from backend.app.db.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    description = Column(Text, nullable=False)
    severity = Column(String(16), default="INFO", nullable=False)  # INFO, WARNING, ERROR, CRITICAL

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "description": self.description,
            "severity": self.severity
        }
