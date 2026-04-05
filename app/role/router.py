from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_permission
from app.database import get_db
from app.role import schemas, service

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[schemas.RoleResponse])
def list_roles(
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db),
    _=Depends(require_permission("roles.view", company_scoped=False)),
):
    return service.get_roles(db, skip=skip, limit=limit)


@router.post("/", response_model=schemas.RoleResponse, status_code=201)
def create_role(
    body: schemas.RoleCreate,
    db=Depends(get_db),
    current_user=Depends(require_permission("roles.create", company_scoped=False)),
):
    return service.create_role(db, body, actor_user_id=current_user["id"])


@router.get("/{role_id}", response_model=schemas.RoleResponse)
def get_role(
    role_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("roles.view", company_scoped=False)),
):
    return service.get_role(db, role_id)


@router.put("/{role_id}", response_model=schemas.RoleResponse)
def update_role(
    role_id: str,
    body: schemas.RoleUpdate,
    db=Depends(get_db),
    current_user=Depends(require_permission("roles.edit", company_scoped=False)),
):
    return service.update_role(db, role_id, body, actor_user_id=current_user["id"])


@router.delete("/{role_id}")
def delete_role(
    role_id: str,
    db=Depends(get_db),
    current_user=Depends(require_permission("roles.delete", company_scoped=False)),
):
    return service.delete_role(db, role_id, actor_user_id=current_user["id"])
