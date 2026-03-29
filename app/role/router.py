from typing import List

from fastapi import APIRouter, Depends
from app.auth.dependencies import require_permission
from app.database import get_db
from app.role import schemas, service

router = APIRouter(prefix="/roles", tags=["roles"])

@router.post("/", response_model=schemas.Role)
def create_role(role_in: schemas.RoleCreate, company_id: int, db=Depends(get_db), current_user=Depends(require_permission("company.roles.manage"))):
    return service.create_role(db=db, role_data=role_in, actor_user_id=current_user["id"], company_id=company_id)


@router.get("/", response_model=List[schemas.Role])
def list_roles(skip: int = 0, limit: int = 100, company_id: int | None = None, db=Depends(get_db), _=Depends(require_permission("company.roles.manage"))):
    return service.get_roles(db=db, skip=skip, limit=limit)


@router.get("/{role_id}", response_model=schemas.Role)
def read_role(role_id: int, company_id: int, db=Depends(get_db), _=Depends(require_permission("company.roles.manage"))):
    return service.get_role(db=db, role_id=role_id)


@router.put("/{role_id}", response_model=schemas.Role)
def update_role(role_id: int, role_in: schemas.RoleUpdate, company_id: int, db=Depends(get_db), current_user=Depends(require_permission("company.roles.manage"))):
    return service.update_role(db=db, role_id=role_id, role_data=role_in, actor_user_id=current_user["id"], company_id=company_id)


@router.delete("/{role_id}", response_model=schemas.Role)
def delete_role(role_id: int, company_id: int, db=Depends(get_db), current_user=Depends(require_permission("company.roles.manage"))):
    return service.delete_role(db=db, role_id=role_id, actor_user_id=current_user["id"], company_id=company_id)
