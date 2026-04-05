from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_permission
from app.company import schemas, service
from app.database import get_db

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/", response_model=schemas.TenantResponse, status_code=201)
def create_company(
    body: schemas.TenantCreate,
    db=Depends(get_db),
    current_user=Depends(require_permission("companies.create", company_scoped=False)),
):
    return service.create_tenant(db, body, created_by=current_user["id"])


@router.get("/", response_model=List[schemas.TenantResponse])
def list_companies(
    skip: int = 0,
    limit: int = 100,
    user_id: str | None = None,
    db=Depends(get_db),
    _=Depends(require_permission("companies.view", company_scoped=False)),
):
    return service.get_tenants(db, skip=skip, limit=limit, user_id=user_id)


@router.get("/{company_id}", response_model=schemas.TenantResponse)
def get_company(
    company_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("companies.view")),
):
    return service.get_tenant(db, company_id)


@router.put("/{company_id}", response_model=schemas.TenantResponse)
def update_company(
    company_id: str,
    body: schemas.TenantUpdate,
    db=Depends(get_db),
    current_user=Depends(require_permission("companies.edit")),
):
    return service.update_tenant(db, company_id, body, actor_user_id=current_user["id"])


@router.delete("/{company_id}")
def delete_company(
    company_id: str,
    db=Depends(get_db),
    current_user=Depends(require_permission("companies.delete")),
):
    return service.delete_tenant(db, company_id, actor_user_id=current_user["id"])


@router.get("/{company_id}/members", response_model=List[schemas.TenantMemberResponse])
def list_members(
    company_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("users.view")),
):
    return service.get_members(db, company_id)


@router.post("/{company_id}/members", response_model=schemas.TenantMemberResponse, status_code=201)
def add_member(
    company_id: str,
    body: schemas.TenantMemberCreate,
    db=Depends(get_db),
    current_user=Depends(require_permission("users.create")),
):
    return service.add_member(db, company_id, body, invited_by=current_user["id"])


@router.delete("/{company_id}/members/{user_id}")
def remove_member(
    company_id: str,
    user_id: str,
    db=Depends(get_db),
    current_user=Depends(require_permission("users.delete")),
):
    return service.remove_member(db, company_id, user_id, actor_user_id=current_user["id"])
