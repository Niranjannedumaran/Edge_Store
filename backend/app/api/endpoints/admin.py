from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.models.audit import AuditEvent
from backend.app.schemas.auth import CreateUserRequest, UserResponse
from backend.app.core.security import hash_password
from backend.app.core.dependencies import require_admin
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/users", response_model=List[UserResponse])
def list_users(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return [UserResponse(**u.to_dict()) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    req: CreateUserRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    role = UserRole.ADMIN.value if req.role == "admin" else UserRole.USER.value
    new_user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    AuditService.log_event(
        db, event_type="USER_CREATED",
        description=f"Administrator '{current_admin.username}' created new user '{new_user.username}' (role: {role})",
        user_id=current_admin.id, username=current_admin.username, severity="INFO"
    )

    return UserResponse(**new_user.to_dict())


@router.delete("/users/{user_id}")
def deactivate_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own administrator account"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    db.commit()

    AuditService.log_event(
        db, event_type="USER_DEACTIVATED",
        description=f"Administrator '{current_admin.username}' deactivated user '{user.username}'",
        user_id=current_admin.id, username=current_admin.username, severity="WARNING"
    )

    return {"message": f"User {user.username} deactivated successfully"}


@router.get("/audit-logs")
def list_audit_logs(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(AuditEvent)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if severity:
        query = query.filter(AuditEvent.severity == severity)

    logs = query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    return [l.to_dict() for l in logs]
