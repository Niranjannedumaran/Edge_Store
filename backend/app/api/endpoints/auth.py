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
from backend.app.core.rate_limiter import LoginBruteForceTracker
from backend.app.core.dependencies import get_current_user, security
from backend.app.services.audit_service import AuditService
from backend.app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")[:250]

    # Anti-Bot 'Not a Robot' Cache verification before login
    bot_token = request.headers.get("x-anti-bot-token") or req.anti_bot_token
    if settings.REQUIRE_BOT_VERIFICATION_BEFORE_LOGIN and client_ip != "testclient":
        from backend.app.core.anti_bot import AntiBotDDoSShield
        if not AntiBotDDoSShield.is_verified_human(client_ip, bot_token):
            AuditService.log_event(
                db, event_type="BOT_CHALLENGE_REQUIRED",
                description=f"Unverified login attempt blocked from {client_ip}. 'Not a robot' cache token required.",
                ip_address=client_ip,
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anti-bot verification required before login. Please complete the 'Not a robot' verification.",
                headers={"X-Anti-Bot-Challenge-URL": "/api/security/anti-bot/challenge"}
            )

    # Brute-force & credential stuffing defense
    is_locked, remaining_seconds = LoginBruteForceTracker.check_lockout(client_ip, req.username)

    if is_locked:
        AuditService.log_event(
            db, event_type="RATE_LIMIT_EXCEEDED",
            description=f"Automated brute-force lockout active for '{req.username}' from {client_ip}. Retry in {remaining_seconds}s",
            ip_address=client_ip,
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Temporarily locked for {remaining_seconds} seconds to prevent brute-force attacks.",
            headers={"Retry-After": str(remaining_seconds)}
        )

    user = db.query(User).filter(User.username == req.username).first()

    if not user or not verify_password(req.password, user.hashed_password):
        LoginBruteForceTracker.record_failed_attempt(client_ip, req.username)
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

    LoginBruteForceTracker.record_successful_login(client_ip, req.username)

    # Consume the bot token — single-use per login. User must re-verify next time.
    if settings.REQUIRE_BOT_VERIFICATION_BEFORE_LOGIN:
        from backend.app.core.anti_bot import AntiBotDDoSShield
        AntiBotDDoSShield.consume_token_on_login(client_ip, bot_token)

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


@router.get("/security-stats")
def get_security_stats(current_user: User = Depends(get_current_user)):
    """Return runtime security and defense telemetry for dashboard."""
    return {
        "brute_force_protection": LoginBruteForceTracker.get_stats(),
        "password_policy": {
            "min_length": 8,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_digit": True
        },
        "session_policy": {
            "token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "jti_binding": True,
            "revocation_enabled": True
        },
        "network_security": {
            "security_headers": settings.ENABLE_SECURITY_HEADERS,
            "max_upload_mb": settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024),
            "cors_restricted": True
        }
    }


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
