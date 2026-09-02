import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from backend.app.config import settings
from backend.app.core.exceptions import AuthenticationException
from backend.app.core.logger import logger


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with automatic salt generation."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


import uuid

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None, jti: Optional[str] = None) -> str:
    """Generate a signed JWT access token with unique JTI session identifier."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    token_jti = jti or str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "edgestore-auth-v1",
        "jti": token_jti
    })

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a signed JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer="edgestore-auth-v1"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Access token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationException("Invalid access token")
