from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_permission
from app.company import schemas, service
from app.database import get_db

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/", response_model=schemas.CompanyResponse)
def create_company(
    company_in: schemas.CompanyCreate,
    db=Depends(get_db),
    current_user=Depends(require_permission("companies.create", company_scoped=False)),
):
    return service.create_company(db, company_in, created_by=current_user["id"])


@router.get("/", response_model=List[schemas.CompanyResponse])
def list_companies(
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
    db=Depends(get_db),
    _=Depends(require_permission("companies.view", company_scoped=False)),
):
    return service.get_companies(db, skip=skip, limit=limit, user_id=user_id)


@router.get("/{company_id}/members", response_model=List[schemas.CompanyMembershipResponse])
def list_company_members(company_id: int, db=Depends(get_db), _=Depends(require_permission("users.view"))):
    return service.get_company_members(db, company_id)


@router.post("/{company_id}/members", response_model=schemas.CompanyMembershipResponse)
def add_company_member(
    company_id: int,
    member_in: schemas.CompanyMembershipCreate,
    db=Depends(get_db),
    current_user=Depends(require_permission("users.assign_permissions")),
):
    return service.add_company_member(db, company_id, member_in, invited_by=current_user["id"])


@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    db=Depends(get_db),
    current_user=Depends(require_permission("companies.delete")),
):
    return service.delete_company(db, company_id, actor_user_id=current_user["id"])


@router.delete("/{company_id}/members/{user_id}")
def remove_company_member(
    company_id: int,
    user_id: int,
    db=Depends(get_db),
    current_user=Depends(require_permission("users.delete")),
):
    return service.remove_company_member(db, company_id, user_id, actor_user_id=current_user["id"])
