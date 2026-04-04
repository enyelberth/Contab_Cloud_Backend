from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class CurrentUserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    tenant_id: str | None = None
    role_id: str | None = None
    status: str
