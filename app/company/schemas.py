from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class CompanyBase(BaseModel):
    legal_name: str
    trade_name: Optional[str] = None
    tax_id: str
    country: str = "VE"
    accounting_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: int
    status: str
    created_by: Optional[int] = None
    created_at: datetime


class CompanyMembershipCreate(BaseModel):
    user_id: int
    role_id: int
    access_level: str = "full"


class CompanyMembershipResponse(BaseModel):
    id: int
    company_id: int
    user_id: int
    role_id: int
    is_primary_accountant: bool
    access_level: str
    status: str
    invited_by: Optional[int] = None
    invited_at: Optional[datetime] = None
    joined_at: datetime
