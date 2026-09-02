from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: Optional[str] = "user"
