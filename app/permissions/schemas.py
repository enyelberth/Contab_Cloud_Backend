from typing import Optional

from pydantic import BaseModel


class PermissionCreate(BaseModel):
    module: str
    name: str
    slug: str
    description: Optional[str] = None


class PermissionResponse(BaseModel):
    id: str
    module: str
    name: str
    slug: str
    description: Optional[str] = None


class PermissionAssign(BaseModel):
    role_id: str
    permission_ids: list[str]
