from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.permissions import schemas
from app.role import schemas as role_schemas
from app.permissions.service import PermissionService # Importamos la clase

router = APIRouter(prefix="/permissions", tags=["permissions"])

# ================================================================
#-- OPERACIONES BÁSICAS (CRUD) DE PERMISOS
# ================================================================

@router.get("/", response_model=List[schemas.Permission])
def list_permissions(db: Session = Depends(get_db)):
    """Lista todos los permisos registrados en Kaizen ERP."""
    # Instanciamos el servicio y llamamos al método
    svc = PermissionService(db)
    return svc.get_permissions()

@router.post("/", response_model=schemas.Permission, status_code=status.HTTP_201_CREATED)
def create_permission(permission_in: schemas.PermissionCreate, db: Session = Depends(get_db)):
    """Crea un nuevo permiso (ej. sales.create)."""
    svc = PermissionService(db)
    return svc.create_permission(permission_in)

@router.get("/{permission_id}", response_model=schemas.Permission)
def get_permission(permission_id: int, db: Session = Depends(get_db)):
    """Obtiene los detalles de un permiso específico."""
    svc = PermissionService(db)
    return svc.get_permission(permission_id)

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(permission_id: int, db: Session = Depends(get_db)):
    """Elimina un permiso del sistema."""
    svc = PermissionService(db)
    svc.delete_permission(permission_id)
    return None # El status 204 no devuelve cuerpo

# ================================================================
#-- CONSULTAS DE ACCESO (RELACIONES)
# ================================================================

@router.get("/{permission_id}", response_model=List[role_schemas.Role])
def get_permission_roles(permission_id: int, db: Session = Depends(get_db)):
    """Muestra qué roles tienen asignado este permiso."""
    svc = PermissionService(db)
    # Asegúrate de tener este método creado en tu clase PermissionService
    return svc.get_permission_roles(permission_id)


# ================================================================
#-- Asignar PERMISOS A ROLES
# ================================================================
@router.post("/assign", response_model=role_schemas.Role)
def assign_permissions_to_role(role_id: int, permission_ids: List[int], db: Session = Depends(get_db)):
    """Asigna una lista de permisos a un rol específico."""
    svc = PermissionService(db)
    return svc.assign_permissions_to_role(role_id, permission_ids) 