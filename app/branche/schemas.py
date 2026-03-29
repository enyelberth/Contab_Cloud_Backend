from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# Esquema base con campos comunes (lo que se comparte entre crear y leer)
class BranchBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

# Esquema para cuando alguien crea una nueva sede (Input)
class BranchCreate(BranchBase):
    pass  # Por ahora no necesitamos campos extra al crear

# Esquema para cuando alguien actualiza una sede (Campos opcionales)
class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

# Esquema que la API devuelve al cliente (Output)
class Branch(BranchBase):
    id: int
    created_at: datetime
    
    # Esto es vital para que Pydantic pueda leer modelos de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)