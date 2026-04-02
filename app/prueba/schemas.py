from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PruebaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None


class Prueba(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    created_at: datetime
