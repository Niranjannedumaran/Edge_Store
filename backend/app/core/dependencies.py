from datetime import datetime, timezone
from typing import Callable, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.session import UserSession
from backend.app.core.security import decode_access_token
from backend.app.core.exceptions import AuthenticationException, AuthorizationException
from backend.app.hal import hal
from backend.app.core.logger import logger

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Validate Bearer JWT, check session revocation, account active state, and guest expiration."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        username: str = payload.get("sub")
        jti: str = payload.get("jti")
        if not username:
            raise AuthenticationException("Token missing subject identifier")
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated"
        )

    if user.is_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Temporary guest account has expired"
        )

    # Check session revocation if JTI is present
    if jti:
        user_session = db.query(UserSession).filter(UserSession.token_jti == jti).first()
        if user_session:
            if user_session.is_revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            # Update last activity
            user_session.last_activity_at = datetime.now(timezone.utc)
            db.commit()

    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Retrieve current user if Bearer token is provided, or None for public client operations."""
    if not credentials:
        return None
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


def require_permission(permission_code: str) -> Callable:
    """Dependency factory enforcing that the authenticated user possesses the specified permission."""
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not current_user.has_permission(permission_code):
            from backend.app.services.audit_service import AuditService
            AuditService.log_event(
                db,
                event_type="ACCESS_DENIED",
                description=f"User '{current_user.username}' (role: {current_user.role}) denied action requiring permission '{permission_code}'",
                user_id=current_user.id,
                username=current_user.username,
                severity="WARNING"
            )
            logger.warning(
                f"Access denied: user='{current_user.username}' lacks permission='{permission_code}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: '{permission_code}'"
            )
        return current_user

    return permission_checker


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Backward-compatible admin check (Super Admin or roles with system.manage)."""
    if current_user.role not in ("super_admin", "admin") and not current_user.has_permission("system.manage"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this operation"
        )
    return current_user


def require_vault_unlocked():
    """Verify that the encrypted storage vault is currently unlocked."""
    if not hal.encryption.is_unlocked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Storage vault is locked. Key-SD unlock required."
        )


def require_storage_operational():
    """Verify that at least one storage provider (Primary or Replica) is operational."""
    primary_ok = hal.primary_storage.is_available()
    replica_ok = hal.replica_storage.is_available()
    if not primary_ok and not replica_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Both primary and replica storage devices are unavailable"
        )
