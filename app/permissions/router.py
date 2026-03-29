from typing import List
from fastapi import APIRouter, Depends, status
from app.auth.dependencies import require_permission
from app.database import get_db
from app.permissions import schemas
from app.role import schemas as role_schemas
from app.permissions.service import PermissionService # Importamos la clase

router = APIRouter(prefix="/permissions", tags=["permissions"])

# ================================================================
#-- OPERACIONES BÁSICAS (CRUD) DE PERMISOS
# ================================================================

@router.get("/", response_model=List[schemas.Permission])
def list_permissions(company_id: int, db=Depends(get_db), _=Depends(require_permission("company.roles.manage"))):
    svc = PermissionService(db)
    return svc.get_permissions()

@router.post("/", response_model=schemas.Permission, status_code=status.HTTP_201_CREATED)
def create_permission(permission_in: schemas.PermissionCreate, company_id: int, db=Depends(get_db), current_user=Depends(require_permission("company.roles.manage"))):
    svc = PermissionService(db)
    return svc.create_permission(permission_in, actor_user_id=current_user["id"], company_id=company_id)

@router.get("/{permission_id}", response_model=schemas.Permission)
def get_permission(permission_id: int, company_id: int, db=Depends(get_db), _=Depends(require_permission("company.roles.manage"))):
    svc = PermissionService(db)
    return svc.get_permission(permission_id)

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(permission_id: int, company_id: int, db=Depends(get_db), current_user=Depends(require_permission("company.roles.manage"))):
    svc = PermissionService(db)
    svc.delete_permission(permission_id, actor_user_id=current_user["id"], company_id=company_id)
    return None

# ================================================================
#-- CONSULTAS DE ACCESO (RELACIONES)
# ================================================================

@router.get("/{permission_id}/roles", response_model=List[role_schemas.Role])
def get_permission_roles(permission_id: int, company_id: int, db=Depends(get_db), _=Depends(require_permission("company.roles.manage"))):
    svc = PermissionService(db)
    return svc.get_permission_roles(permission_id)


# ================================================================
#-- Asignar PERMISOS A ROLES
# ================================================================
@router.post("/assign", response_model=role_schemas.Role)
def assign_permissions_to_role(role_id: int, permission_ids: List[int], company_id: int, db=Depends(get_db), current_user=Depends(require_permission("users.assign_permissions"))):
    svc = PermissionService(db)
    return svc.assign_permissions_to_role(role_id, permission_ids, actor_user_id=current_user["id"], company_id=company_id)