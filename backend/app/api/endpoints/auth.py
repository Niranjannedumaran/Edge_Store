from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from backend.app.core.security import verify_password, create_access_token
from backend.app.core.dependencies import get_current_user
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        AuditService.log_event(
            db, event_type="LOGIN_FAILED",
            description=f"Failed login attempt for username '{req.username}'",
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(data={"sub": user.username, "role": user.role, "id": user.id})

    AuditService.log_event(
        db, event_type="LOGIN_SUCCESS",
        description=f"User '{user.username}' logged in successfully",
        user_id=user.id, username=user.username, severity="INFO"
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user.to_dict()
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(**current_user.to_dict())


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    AuditService.log_event(
        db, event_type="LOGOUT",
        description=f"User '{current_user.username}' logged out",
        user_id=current_user.id, username=current_user.username, severity="INFO"
    )
    return {"message": "Logged out successfully"}
