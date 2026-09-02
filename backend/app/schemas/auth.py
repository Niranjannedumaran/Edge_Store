from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: str
    role_name: Optional[str] = None
    is_active: bool
    is_expired: Optional[bool] = False
    expires_at: Optional[str] = None
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None
    permissions: Optional[List[str]] = []


class CreateUserRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = "file_manager"
    is_temporary: Optional[bool] = False
    expires_in_hours: Optional[int] = None


class UpdateUserRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class ResetPasswordRequest(BaseModel):
    new_password: str


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str
    description: Optional[str] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    is_system: bool
    permissions: List[str] = []


class UpdateRolePermissionsRequest(BaseModel):
    permission_codes: List[str]


class SessionResponse(BaseModel):
    id: int
    user_id: int
    username: str
    token_jti: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[str] = None
    last_activity_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_revoked: bool
