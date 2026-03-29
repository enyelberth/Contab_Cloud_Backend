from pydantic import BaseModel, ConfigDict
from typing import Optional, List

# --- ESQUEMAS DE PERMISOS ---
class PermissionBase(BaseModel):
    name: str
    slug: str

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None

class Permission(PermissionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

