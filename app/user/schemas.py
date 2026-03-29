from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_type: str = "accountant"
    branch_id: Optional[int] = None
    role_id: Optional[int] = None
    status: Optional[str] = "active"

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_type: Optional[str] = None
    password: Optional[str] = None
    branch_id: Optional[int] = None
    role_id: Optional[int] = None
    status: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    company_id: Optional[int] = None

    class Config:
        from_attributes = True