from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel
from app.meses.schemas import Mes


class EjercicioCreate(BaseModel):
    ano: str
    fecha_i: datetime
    fecha_f: datetime
    obser: Optional[str] = None
    status: Optional[str] = None
    bloqueo: Optional[str] = None


class EjercicioUpdate(BaseModel):
    ano: Optional[str] = None
    fecha_i: Optional[datetime] = None
    fecha_f: Optional[datetime] = None
    obser: Optional[str] = None
    status: Optional[str] = None
    bloqueo: Optional[str] = None


class Ejercicio(BaseModel):
    id: int
    ano: Optional[str] = None
    fecha_i: Optional[datetime] = None
    fecha_f: Optional[datetime] = None
    obser: Optional[str] = None
    status: Optional[str] = None
    bloqueo: Optional[str] = None


class EjercicioCreado(BaseModel):
    ejercicio: Ejercicio
    meses_creados: List[Mes]
