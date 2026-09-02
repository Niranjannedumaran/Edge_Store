from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.audit import AuditEvent
from backend.app.core.logger import logger


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        description: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        severity: str = "INFO"
    ) -> AuditEvent:
        """Persist an audit log entry while keeping sensitive secrets out."""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            description=description,
            severity=severity
        )
        try:
            db.add(event)
            db.commit()
            db.refresh(event)
            logger.info(f"[AUDIT] [{severity}] {event_type} by {username or 'SYSTEM'}: {description}")
            return event
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to persist audit log: {e}")
            raise
