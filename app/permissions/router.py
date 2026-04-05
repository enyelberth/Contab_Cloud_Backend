from typing import List

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import require_permission
from app.database import get_db
from app.permissions import schemas, service

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("/", response_model=List[schemas.PermissionResponse])
def list_permissions(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db),
    _=Depends(require_permission("roles.view", company_scoped=False)),
):
    return service.get_permissions(db, skip=skip, limit=limit)


@router.post("/", response_model=schemas.PermissionResponse, status_code=status.HTTP_201_CREATED)
def create_permission(
    body: schemas.PermissionCreate,
    db=Depends(get_db),
    current_user=Depends(require_permission("roles.create", company_scoped=False)),
):
    return service.create_permission(db, body, actor_user_id=current_user["id"])


@router.get("/{permission_id}", response_model=schemas.PermissionResponse)
def get_permission(
    permission_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("roles.view", company_scoped=False)),
):
    return service.get_permission(db, permission_id)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(
    permission_id: str,
    db=Depends(get_db),
    current_user=Depends(require_permission("roles.delete", company_scoped=False)),
):
    service.delete_permission(db, permission_id, actor_user_id=current_user["id"])
    return None


@router.post("/assign")
def assign_permissions(
    body: schemas.PermissionAssign,
    db=Depends(get_db),
    current_user=Depends(require_permission("roles.edit", company_scoped=False)),
):
    return service.assign_permissions_to_role(db, body, actor_user_id=current_user["id"])


@router.get("/roles/{role_id}")
def get_role_permissions(
    role_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("roles.view", company_scoped=False)),
):
    return service.get_role_permissions(db, role_id)
