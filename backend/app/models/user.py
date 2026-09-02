from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    STORAGE_ADMIN = "storage_admin"
    SECURITY_ADMIN = "security_admin"
    FILE_MANAGER = "file_manager"
    GUEST = "guest"
    # Legacy compatibility aliases
    ADMIN = "super_admin"
    USER = "file_manager"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    display_name = Column(String(128), nullable=True)
    email = Column(String(128), unique=True, index=True, nullable=True)
    hashed_password = Column(String(256), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    role = Column(String(32), default=UserRole.FILE_MANAGER.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # For temporary Guest accounts
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    role_obj = relationship("Role", back_populates="users", lazy="joined")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def has_permission(self, permission_code: str) -> bool:
        """Check if user possesses the specified permission code."""
        if not self.is_active or self.is_expired():
            return False
        # Super admin has unconditional access
        if self.role in ("super_admin", "admin"):
            return True
        if self.role_obj and self.role_obj.permissions:
            return any(p.code == permission_code for p in self.role_obj.permissions)
        return False

    def is_expired(self) -> bool:
        """Check if a temporary account has passed its expiration timestamp."""
        if self.expires_at is None:
            return False
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires

    def get_permissions(self):
        """Return list of active permission codes."""
        if not self.is_active or self.is_expired():
            return []
        if self.role in ("super_admin", "admin"):
            # Return all permissions if super admin
            if self.role_obj and self.role_obj.permissions:
                return [p.code for p in self.role_obj.permissions]
            from backend.app.models.role import Permission
            return [p.code for p in Permission.__table__.columns]
        if self.role_obj and self.role_obj.permissions:
            return [p.code for p in self.role_obj.permissions]
        return []

    def to_dict(self):
        perms = []
        if self.role_obj and self.role_obj.permissions:
            perms = [p.code for p in self.role_obj.permissions]

        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name or self.username,
            "email": self.email,
            "role": self.role,
            "role_name": self.role_obj.display_name if self.role_obj else self.role,
            "is_active": self.is_active,
            "is_expired": self.is_expired(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "permissions": perms
        }
