from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel


# ─────────────────────────────────────────────
# Detalle de Comprobante
# ─────────────────────────────────────────────

class DetalleComprobanteCreate(BaseModel):
    num_item: Optional[int] = None
    txt_cuenta: str
    nom_corto: Optional[str] = None
    txt_tipo: Optional[str] = None
    txt_referencia: Optional[str] = None
    txt_concepto: Optional[str] = None
    num_debito: Decimal = Decimal("0")
    num_credito: Decimal = Decimal("0")
    fecha: Optional[datetime] = None
    auxiliar: int = 0
    tipo_auxiliar: str = ""


class DetalleComprobanteUpdate(BaseModel):
    num_item: Optional[int] = None
    txt_cuenta: Optional[str] = None
    nom_corto: Optional[str] = None
    txt_tipo: Optional[str] = None
    txt_referencia: Optional[str] = None
    txt_concepto: Optional[str] = None
    num_debito: Optional[Decimal] = None
    num_credito: Optional[Decimal] = None
    fecha: Optional[datetime] = None
    auxiliar: Optional[int] = None
    tipo_auxiliar: Optional[str] = None


class DetalleComprobante(BaseModel):
    id: int
    num_comprobante: int
    num_item: Optional[int] = None
    txt_cuenta: str
    nom_corto: Optional[str] = None
    txt_tipo: Optional[str] = None
    txt_referencia: Optional[str] = None
    txt_concepto: Optional[str] = None
    num_debito: Decimal
    num_credito: Decimal
    fecha: Optional[datetime] = None
    auxiliar: int
    tipo_auxiliar: str


# ─────────────────────────────────────────────
# Maestro de Comprobante
# ─────────────────────────────────────────────

class MaestroComprobanteCreate(BaseModel):
    fecha_comprobante: Optional[datetime] = None
    tipo: Optional[str] = None
    txt_descripcion: Optional[str] = None
    txt_status: Optional[int] = None
    txt_id_usuario: Optional[str] = None
    txt_id_pc: Optional[str] = None
    txt_modo_creacion: Optional[str] = None
    txt_comentario: Optional[str] = None
    clase: Optional[str] = None
    num_comp: Optional[str] = None
    num_transferencia: Optional[int] = None
    sg_moneda: Optional[str] = None
    n_tipo: Optional[str] = None
    n_sub_tipo: Optional[str] = None
    num_operacion_comp: Optional[int] = None
    detalles: Optional[List[DetalleComprobanteCreate]] = None


class MaestroComprobanteUpdate(BaseModel):
    fecha_comprobante: Optional[datetime] = None
    tipo: Optional[str] = None
    txt_descripcion: Optional[str] = None
    txt_status: Optional[int] = None
    txt_id_usuario: Optional[str] = None
    txt_id_pc: Optional[str] = None
    txt_modo_creacion: Optional[str] = None
    txt_comentario: Optional[str] = None
    clase: Optional[str] = None
    num_comp: Optional[str] = None
    num_transferencia: Optional[int] = None
    sg_moneda: Optional[str] = None
    n_tipo: Optional[str] = None
    n_sub_tipo: Optional[str] = None
    num_operacion_comp: Optional[int] = None
    usuario_anulo: Optional[str] = None
    fecha_hora_anulo: Optional[datetime] = None
    usuario_modifico: Optional[str] = None
    fecha_hora_modifico: Optional[datetime] = None


class MaestroComprobante(BaseModel):
    num_comprobante: int
    fecha_comprobante: Optional[datetime] = None
    tipo: Optional[str] = None
    txt_descripcion: Optional[str] = None
    txt_status: Optional[int] = None
    txt_id_usuario: Optional[str] = None
    fecha_hora_creacion: Optional[datetime] = None
    txt_id_pc: Optional[str] = None
    txt_modo_creacion: Optional[str] = None
    txt_comentario: Optional[str] = None
    clase: Optional[str] = None
    num_comp: Optional[str] = None
    num_transferencia: Optional[int] = None
    sg_moneda: Optional[str] = None
    n_tipo: Optional[str] = None
    n_sub_tipo: Optional[str] = None
    num_operacion_comp: Optional[int] = None
    usuario_anulo: Optional[str] = None
    fecha_hora_anulo: Optional[datetime] = None
    usuario_modifico: Optional[str] = None
    fecha_hora_modifico: Optional[datetime] = None


class MaestroComprobanteConDetalles(MaestroComprobante):
    detalles: List[DetalleComprobante] = []


class MaestroComprobanteCreado(BaseModel):
    comprobante: MaestroComprobante
    detalles: List[DetalleComprobante] = []
