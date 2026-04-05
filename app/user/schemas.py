from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: Optional[str] = None
    first_lastname: Optional[str] = None
    phone: Optional[str] = None
    role_id: str  # UUID del rol en el tenant


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    first_lastname: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6)
    status: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    first_lastname: Optional[str] = None
    phone: Optional[str] = None
    status: str
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    tenant_id: Optional[str] = None
    created_at: datetime
