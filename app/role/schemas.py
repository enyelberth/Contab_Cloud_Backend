from typing import List, Optional

from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    level: int = 100
    is_system: bool = False


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    level: Optional[int] = None


class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    level: int
    is_system: bool
