from typing import List

from pydantic import BaseModel


class MenuAccessItem(BaseModel):
    menu_id: int
    menu_key: str
    label: str
    path: str
    icon: str | None = None
    module_key: str
    module_name: str
    can_view: bool
    can_create: bool
    can_update: bool
    can_delete: bool
    can_assign_permissions: bool


class UserMenusResponse(BaseModel):
    user_id: str
    company_id: str
    role_id: str
    role_name: str
    menus: List[MenuAccessItem]


class PermissionItem(BaseModel):
    id: str
    name: str
    slug: str


class UserPermissionsResponse(BaseModel):
    user_id: str
    company_id: str
    role_id: str
    role_name: str
    permissions: List[PermissionItem]


class DelegationCheckResponse(BaseModel):
    manager_user_id: str
    company_id: str
    manager_role_id: str
    target_role_id: str
    can_assign_role: bool
    can_grant_permissions: bool
