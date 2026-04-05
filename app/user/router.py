from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_permission
from app.database import get_db
from app.user import schemas, service

router = APIRouter(prefix="/companies/{company_id}/users", tags=["users"])


@router.get("/", response_model=List[schemas.UserResponse])
def list_users(
    company_id: str,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db),
    _=Depends(require_permission("users.view")),
):
    return service.get_users(db, tenant_id=company_id, skip=skip, limit=limit)


@router.post("/", response_model=schemas.UserResponse, status_code=201)
def create_user(
    company_id: str,
    body: schemas.UserCreate,
    db=Depends(get_db),
    current_user=Depends(require_permission("users.create")),
):
    return service.create_user(db, tenant_id=company_id, data=body, actor_user_id=current_user["id"])


@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    company_id: str,
    user_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("users.view")),
):
    return service.get_user(db, tenant_id=company_id, user_id=user_id)


@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    company_id: str,
    user_id: str,
    body: schemas.UserUpdate,
    db=Depends(get_db),
    current_user=Depends(require_permission("users.edit")),
):
    return service.update_user(db, tenant_id=company_id, user_id=user_id, data=body, actor_user_id=current_user["id"])


@router.delete("/{user_id}")
def delete_user(
    company_id: str,
    user_id: str,
    db=Depends(get_db),
    current_user=Depends(require_permission("users.delete")),
):
    return service.delete_user(db, tenant_id=company_id, user_id=user_id, actor_user_id=current_user["id"])
