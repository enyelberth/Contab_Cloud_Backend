from typing import List, Optional

from pydantic import BaseModel


class CuentaCreate(BaseModel):
    txt_cuenta: str
    txt_denominacion: Optional[str] = None
    txt_nom_corto: Optional[str] = None
    num_nivel: Optional[int] = None
    txt_status: Optional[str] = None
    txt_comentario: Optional[str] = ""
    cuenta_padre: Optional[str] = None
    nomb_cuenta_padre: Optional[str] = None
    num_tipo_aux: Optional[int] = -1
    tipo_aux: Optional[str] = ""
    num_tipo_cuenta: Optional[int] = -1
    cod_tipo_aux: Optional[str] = ""
    num_aux: Optional[int] = -1


class CuentaUpdate(BaseModel):
    txt_denominacion: Optional[str] = None
    txt_nom_corto: Optional[str] = None
    num_nivel: Optional[int] = None
    txt_status: Optional[str] = None
    txt_comentario: Optional[str] = None
    cuenta_padre: Optional[str] = None
    nomb_cuenta_padre: Optional[str] = None
    num_tipo_aux: Optional[int] = None
    tipo_aux: Optional[str] = None
    num_tipo_cuenta: Optional[int] = None
    cod_tipo_aux: Optional[str] = None
    num_aux: Optional[int] = None


class Cuenta(BaseModel):
    id: int
    txt_cuenta: str
    txt_denominacion: Optional[str] = None
    txt_nom_corto: Optional[str] = None
    num_nivel: Optional[int] = None
    txt_status: Optional[str] = None
    txt_comentario: Optional[str] = None
    cuenta_padre: Optional[str] = None
    nomb_cuenta_padre: Optional[str] = None
    num_tipo_aux: Optional[int] = None
    tipo_aux: Optional[str] = None
    num_tipo_cuenta: Optional[int] = None
    cod_tipo_aux: Optional[str] = None
    num_aux: Optional[int] = None


# ------------------------------------------------------------------
# Schemas para comparación entre schemas
# ------------------------------------------------------------------
class ResumenComparacion(BaseModel):
    total_origen: int
    total_destino: int
    solo_en_origen: int
    solo_en_destino: int
    en_ambas: int


class ComparacionCuentas(BaseModel):
    empresa_origen: str
    empresa_destino: str
    resumen: ResumenComparacion
    solo_en_origen: List[Cuenta]
    solo_en_destino: List[Cuenta]
    en_ambas: List[Cuenta]


# ------------------------------------------------------------------
# Schemas para operaciones masivas
# ------------------------------------------------------------------
class LoteResultado(BaseModel):
    insertadas: int
    omitidas: int
    cuentas: List[Cuenta]


class ImportarResultado(BaseModel):
    empresa_origen: str
    empresa_destino: str
    modo: str
    importadas: int
    cuentas: List[Cuenta]
