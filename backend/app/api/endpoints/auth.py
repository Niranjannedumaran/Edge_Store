import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.models.session import UserSession
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserResponse, SessionResponse
from backend.app.core.security import verify_password, create_access_token, decode_access_token
from backend.app.core.dependencies import get_current_user, security
from backend.app.services.audit_service import AuditService
from backend.app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")[:250]

    if not user or not verify_password(req.password, user.hashed_password):
        AuditService.log_event(
            db, event_type="LOGIN_FAILED",
            description=f"Failed login attempt for username '{req.username}' from {client_ip}",
            ip_address=client_ip,
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        AuditService.log_event(
            db, event_type="LOGIN_FAILED",
            description=f"Login attempt on deactivated account '{req.username}' from {client_ip}",
            ip_address=client_ip,
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    if user.is_expired():
        AuditService.log_event(
            db, event_type="LOGIN_FAILED",
            description=f"Login attempt on expired guest account '{req.username}' from {client_ip}",
            ip_address=client_ip,
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Temporary guest account has expired"
        )

    # Generate session and token with unique JTI
    session_jti = str(uuid.uuid4())
    session_expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    new_session = UserSession(
        user_id=user.id,
        token_jti=session_jti,
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=session_expires,
        is_revoked=False
    )
    db.add(new_session)

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        data={"sub": user.username, "role": user.role, "id": user.id},
        jti=session_jti
    )

    AuditService.log_event(
        db, event_type="LOGIN_SUCCESS",
        description=f"User '{user.username}' (role: {user.role}) logged in successfully from {client_ip}",
        user_id=user.id, username=user.username, ip_address=client_ip, severity="INFO"
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user.to_dict()
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.to_dict())


@router.get("/my-sessions")
def get_my_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False
    ).order_by(UserSession.last_activity_at.desc()).all()
    return [s.to_dict() for s in sessions]


@router.post("/logout")
def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if credentials:
        try:
            payload = decode_access_token(credentials.credentials)
            jti = payload.get("jti")
            if jti:
                user_session = db.query(UserSession).filter(UserSession.token_jti == jti).first()
                if user_session:
                    user_session.is_revoked = True
                    db.commit()
        except Exception:
            pass

    AuditService.log_event(
        db, event_type="LOGOUT",
        description=f"User '{current_user.username}' logged out",
        user_id=current_user.id, username=current_user.username, severity="INFO"
    )
    return {"message": "Logged out successfully"}
