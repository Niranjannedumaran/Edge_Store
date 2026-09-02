from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.models.role import Role, Permission
from backend.app.models.session import UserSession
from backend.app.models.audit import AuditEvent
from backend.app.schemas.auth import (
    CreateUserRequest,
    UpdateUserRequest,
    ResetPasswordRequest,
    UserResponse,
    RoleResponse,
    PermissionResponse,
    UpdateRolePermissionsRequest,
    SessionResponse
)
from backend.app.core.security import hash_password
from backend.app.core.dependencies import require_permission
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Administration"])


# --- USER MANAGEMENT ---

@router.get("/users", response_model=List[UserResponse])
def list_users(
    current_admin: User = Depends(require_permission("users.read")),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserResponse(**u.to_dict()) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    req: CreateUserRequest,
    current_admin: User = Depends(require_permission("users.create")),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Resolve role
    target_role_name = req.role or "file_manager"
    role_obj = db.query(Role).filter(Role.name == target_role_name).first()
    if not role_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{target_role_name}' does not exist"
        )

    # Cannot grant permissions higher than own role (unless Super Admin)
    if current_admin.role not in ("super_admin", "admin") and target_role_name in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a user with a role higher than your own"
        )

    # Expiration for temporary accounts
    expires_at = None
    if req.is_temporary and req.expires_in_hours and req.expires_in_hours > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=req.expires_in_hours)

    new_user = User(
        username=req.username,
        display_name=req.display_name or req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=role_obj.name,
        role_id=role_obj.id,
        is_active=True,
        expires_at=expires_at
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    AuditService.log_event(
        db, event_type="USER_CREATED",
        description=f"User '{current_admin.username}' created account '{new_user.username}' (role: {role_obj.name}, temporary={req.is_temporary})",
        user_id=current_admin.id, username=current_admin.username, severity="INFO"
    )

    return UserResponse(**new_user.to_dict())


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    req: UpdateUserRequest,
    current_admin: User = Depends(require_permission("users.update")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if req.display_name is not None:
        user.display_name = req.display_name
    if req.email is not None:
        user.email = req.email
    if req.is_active is not None:
        if user.id == current_admin.id and not req.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own administrator account"
            )
        user.is_active = req.is_active

    if req.role is not None:
        role_obj = db.query(Role).filter(Role.name == req.role).first()
        if not role_obj:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role '{req.role}' not found")
        user.role = role_obj.name
        user.role_id = role_obj.id

    db.commit()
    db.refresh(user)

    AuditService.log_event(
        db, event_type="USER_MODIFIED",
        description=f"User '{current_admin.username}' updated profile of '{user.username}'",
        user_id=current_admin.id, username=current_admin.username, severity="INFO"
    )

    return UserResponse(**user.to_dict())


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    req: ResetPasswordRequest,
    current_admin: User = Depends(require_permission("users.reset_password")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = hash_password(req.new_password)
    db.commit()

    AuditService.log_event(
        db, event_type="PASSWORD_RESET",
        description=f"Password for user '{user.username}' reset by '{current_admin.username}'",
        user_id=current_admin.id, username=current_admin.username, severity="WARNING"
    )

    return {"message": f"Password for {user.username} has been reset"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_admin: User = Depends(require_permission("users.delete")),
    db: Session = Depends(get_db)
):
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own administrator account"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    username = user.username
    db.delete(user)
    db.commit()

    AuditService.log_event(
        db, event_type="USER_DELETED",
        description=f"User '{username}' deleted permanently by '{current_admin.username}'",
        user_id=current_admin.id, username=current_admin.username, severity="WARNING"
    )

    return {"message": f"User {username} deleted successfully"}


# --- ROLES & PERMISSIONS ---

@router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    current_admin: User = Depends(require_permission("roles.read")),
    db: Session = Depends(get_db)
):
    roles = db.query(Role).all()
    return [RoleResponse(**r.to_dict()) for r in roles]


@router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(
    current_admin: User = Depends(require_permission("roles.read")),
    db: Session = Depends(get_db)
):
    perms = db.query(Permission).order_by(Permission.category.asc(), Permission.code.asc()).all()
    return [PermissionResponse(**p.to_dict()) for p in perms]


@router.put("/roles/{role_id}/permissions", response_model=RoleResponse)
def update_role_permissions(
    role_id: int,
    req: UpdateRolePermissionsRequest,
    current_admin: User = Depends(require_permission("roles.update")),
    db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if role.name == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify immutable system Super Admin role"
        )

    # Fetch permissions
    matched_perms = db.query(Permission).filter(Permission.code.in_(req.permission_codes)).all()
    role.permissions = matched_perms
    db.commit()
    db.refresh(role)

    AuditService.log_event(
        db, event_type="ROLE_PERMISSIONS_MODIFIED",
        description=f"User '{current_admin.username}' updated permissions for role '{role.display_name}' ({len(matched_perms)} assigned)",
        user_id=current_admin.id, username=current_admin.username, severity="WARNING"
    )

    return RoleResponse(**role.to_dict())


# --- SESSION MANAGEMENT ---

@router.get("/sessions", response_model=List[SessionResponse])
def list_active_sessions(
    current_admin: User = Depends(require_permission("users.read")),
    db: Session = Depends(get_db)
):
    sessions = db.query(UserSession).order_by(UserSession.last_activity_at.desc()).limit(100).all()
    return [SessionResponse(**s.to_dict()) for s in sessions]


@router.post("/sessions/{session_id}/revoke")
def revoke_session(
    session_id: int,
    current_admin: User = Depends(require_permission("users.revoke_sessions")),
    db: Session = Depends(get_db)
):
    sess = db.query(UserSession).filter(UserSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    sess.is_revoked = True
    db.commit()

    AuditService.log_event(
        db, event_type="SESSION_REVOKED",
        description=f"Session {sess.token_jti[:8]}... for user '{sess.user.username}' revoked by '{current_admin.username}'",
        user_id=current_admin.id, username=current_admin.username, severity="WARNING"
    )

    return {"message": "Session revoked successfully"}


# --- AUDIT LOGS ---

@router.get("/audit-logs")
def list_audit_logs(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    current_admin: User = Depends(require_permission("audit.read")),
    db: Session = Depends(get_db)
):
    query = db.query(AuditEvent)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if severity:
        query = query.filter(AuditEvent.severity == severity)

    logs = query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    return [l.to_dict() for l in logs]
