from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class MesCreate(BaseModel):
    n_mes_contble: Optional[int] = None
    n_mes_sistema: Optional[int] = None
    mes: Optional[str] = None
    ano: Optional[str] = None
    status: Optional[str] = None
    bloqueo: Optional[str] = None
    ejercicio: Optional[str] = None
    tipo: Optional[str] = None
    usuario: Optional[str] = None
    fecha_i: Optional[datetime] = None
    fecha_f: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    fecha_creado: Optional[datetime] = None


class MesUpdate(BaseModel):
    n_mes_contble: Optional[int] = None
    n_mes_sistema: Optional[int] = None
    mes: Optional[str] = None
    ano: Optional[str] = None
    status: Optional[str] = None
    bloqueo: Optional[str] = None
    ejercicio: Optional[str] = None
    tipo: Optional[str] = None
    usuario: Optional[str] = None
    fecha_i: Optional[datetime] = None
    fecha_f: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    fecha_creado: Optional[datetime] = None


class Mes(BaseModel):
    id: int
    n_mes_contble: Optional[int] = None
    n_mes_sistema: Optional[int] = None
    mes: Optional[str] = None
    ano: Optional[str] = None
    status: Optional[str] = None
    bloqueo: Optional[str] = None
    ejercicio: Optional[str] = None
    tipo: Optional[str] = None
    usuario: Optional[str] = None
    fecha_i: Optional[datetime] = None
    fecha_f: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    fecha_creado: Optional[datetime] = None
