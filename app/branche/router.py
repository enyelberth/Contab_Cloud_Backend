from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_permission
from app.branche import schemas, service
from app.database import get_db

router = APIRouter(prefix="/companies/{company_id}/branches", tags=["branches"])


@router.get("/", response_model=List[schemas.BranchResponse])
def list_branches(
    company_id: str,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db),
    _=Depends(require_permission("branches.view")),
):
    return service.get_branches(db, tenant_id=company_id, skip=skip, limit=limit)


@router.post("/", response_model=schemas.BranchResponse, status_code=201)
def create_branch(
    company_id: str,
    body: schemas.BranchCreate,
    db=Depends(get_db),
    current_user=Depends(require_permission("branches.create")),
):
    return service.create_branch(db, tenant_id=company_id, data=body, actor_user_id=current_user["id"])


@router.get("/{branch_id}", response_model=schemas.BranchResponse)
def get_branch(
    company_id: str,
    branch_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("branches.view")),
):
    return service.get_branch(db, tenant_id=company_id, branch_id=branch_id)


@router.put("/{branch_id}", response_model=schemas.BranchResponse)
def update_branch(
    company_id: str,
    branch_id: str,
    body: schemas.BranchUpdate,
    db=Depends(get_db),
    current_user=Depends(require_permission("branches.edit")),
):
    return service.update_branch(db, tenant_id=company_id, branch_id=branch_id, data=body, actor_user_id=current_user["id"])


@router.delete("/{branch_id}")
def delete_branch(
    company_id: str,
    branch_id: str,
    db=Depends(get_db),
    current_user=Depends(require_permission("branches.delete")),
):
    return service.delete_branch(db, tenant_id=company_id, branch_id=branch_id, actor_user_id=current_user["id"])
