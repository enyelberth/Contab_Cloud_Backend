from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Esquema base con los campos comunes
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    branch_id: int
    role_id: int
    status: Optional[str] = "active"

# Esquema para la creación (aquí pedimos el password)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# Esquema para actualización (todo es opcional)
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    branch_id: Optional[int] = None
    role_id: Optional[int] = None
    status: Optional[str] = None

# Esquema de respuesta (lo que sale hacia la API)
class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True # Esto permite leer el modelo de SQLAlchemy directamente