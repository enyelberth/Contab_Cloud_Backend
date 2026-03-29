from pydantic import BaseModel, ConfigDict
from typing import Optional, List

from app.permissions.schemas import Permission


# --- ESQUEMAS DE ROLES ---
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    scope: str = "company"
    is_assignable_to_client: bool = False

class RoleCreate(RoleBase):
    # Opcional: permitir enviar una lista de IDs de permisos al crear el rol
    permissions_ids: Optional[List[int]] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions_ids: Optional[List[int]] = None

class Role(RoleBase):
    id: int
    # CORRECCIÓN CLAVE: El esquema de salida debe incluir la lista de permisos
    # Usamos el esquema 'Permission' definido arriba para la serialización
    permissions: List[Permission] = [] 
    
    model_config = ConfigDict(from_attributes=True)