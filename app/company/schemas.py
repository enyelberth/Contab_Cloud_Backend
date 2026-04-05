from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class TenantCreate(BaseModel):
    name: str
    slug: str
    rif: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    plan: str = "enterprise"


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    rif: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    plan: Optional[str] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    rif: Optional[str] = None
    address: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: str
    plan: str
    schema_name: str
    created_at: datetime


class TenantMemberCreate(BaseModel):
    user_id: str
    role_id: str


class TenantMemberResponse(BaseModel):
    user_id: str
    tenant_id: str
    role_id: str
    role_name: str
    username: str
    email: str
    first_name: Optional[str] = None
    first_lastname: Optional[str] = None
    is_active: bool
    joined_at: Optional[datetime] = None
