from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.core.security import decode_access_token
from backend.app.core.exceptions import AuthenticationException, AuthorizationException, VaultLockedException, StorageUnavailableException
from backend.app.hal import hal

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        username: str = payload.get("sub")
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

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this operation"
        )
    return current_user


def require_vault_unlocked():
    """Verify that the encrypted vault is currently unlocked."""
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
