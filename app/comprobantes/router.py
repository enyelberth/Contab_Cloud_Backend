from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_permission
from app.database import get_db
from app.comprobantes import schemas, service

router = APIRouter(
    prefix="/companies/{company_id}/comprobantes",
    tags=["comprobantes"],
)


# ──────────────────────────────────────────────────────────────
# Maestro de Comprobantes
# ──────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[schemas.MaestroComprobante],
    summary="Listar comprobantes contables de una empresa",
)
def listar_comprobantes(
    company_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("comprobantes.view")),
):
    return service.get_comprobantes(db, company_id)


@router.post(
    "/",
    response_model=schemas.MaestroComprobanteCreado,
    status_code=201,
    summary="Crear un comprobante contable",
    description=(
        "Crea el maestro del comprobante. "
        "Si se incluye el campo **detalles**, se insertan las líneas contables en el mismo request."
    ),
)
def crear_comprobante(
    company_id: str,
    data: schemas.MaestroComprobanteCreate,
    db=Depends(get_db),
    _=Depends(require_permission("comprobantes.create")),
):
    return service.crear_comprobante(db, company_id, data)


@router.get(
    "/{num_comprobante}",
    response_model=schemas.MaestroComprobanteConDetalles,
    summary="Obtener un comprobante con sus detalles",
)
def obtener_comprobante(
    company_id: str,
    num_comprobante: int,
    db=Depends(get_db),
    _=Depends(require_permission("comprobantes.view")),
):
    return service.get_comprobante_con_detalles(db, company_id, num_comprobante)


@router.put(
    "/{num_comprobante}",
    response_model=schemas.MaestroComprobante,
    summary="Actualizar un comprobante contable",
)
def actualizar_comprobante(
    company_id: str,
    num_comprobante: int,
    data: schemas.MaestroComprobanteUpdate,
    db=Depends(get_db),
    _=Depends(require_permission("comprobantes.edit")),
):
    return service.actualizar_comprobante(db, company_id, num_comprobante, data)


@router.delete(
    "/{num_comprobante}",
    summary="Eliminar un comprobante y todos sus detalles",
)
def eliminar_comprobante(
    company_id: str,
    num_comprobante: int,
    db=Depends(get_db),
    _=Depends(require_permission("comprobantes.delete")),
):
    return service.eliminar_comprobante(db, company_id, num_comprobante)


# ──────────────────────────────────────────────────────────────
# Detalle de Comprobante
# ──────────────────────────────────────────────────────────────

@router.get(
    "/{num_comprobante}/detalles",
    response_model=List[schemas.DetalleComprobante],
    summary="Listar líneas de un comprobante",
)
def listar_detalles(
    company_id: str,
    num_comprobante: int,
    db=Depends(get_db),
    _=Depends(require_permission("comprobantes.view")),
):
    return service.get_detalles(db, company_id, num_comprobante)


@router.post(
    "/{num_comprobante}/detalles",
    response_model=schemas.DetalleComprobante,
    status_code=201,
    summary="Agregar una línea a un comprobante",
)
def agregar_detalle(
    company_id: str,
    num_comprobante: int,
    data: schemas.DetalleComprobanteCreate,
    db=Depends(get_db),
    _=Depends(require_permission("comprobantes.create")),
):
    return service.agregar_detalle(db, company_id, num_comprobante, data)


@router.get(
    "/{num_comprobante}/detalles/{detalle_id}",
    response_model=schemas.DetalleComprobante,
    summary="Obtener una línea de un comprobante",
)
def obtener_detalle(
    company_id: str,
    num_comprobante: int,
    detalle_id: int,
    db=Depends(get_db),
    _=Depends(require_permission("comprobantes.view")),
):
    return service.get_detalle(db, company_id, num_comprobante, detalle_id)


@router.put(
    "/{num_comprobante}/detalles/{detalle_id}",
    response_model=schemas.DetalleComprobante,
    summary="Actualizar una línea de un comprobante",
)
def actualizar_detalle(
    company_id: str,
    num_comprobante: int,
    detalle_id: int,
    data: schemas.DetalleComprobanteUpdate,
    db=Depends(get_db),
    _=Depends(require_permission("comprobantes.edit")),
):
    return service.actualizar_detalle(db, company_id, num_comprobante, detalle_id, data)


@router.delete(
    "/{num_comprobante}/detalles/{detalle_id}",
    summary="Eliminar una línea de un comprobante",
)
def eliminar_detalle(
    company_id: str,
    num_comprobante: int,
    detalle_id: int,
    db=Depends(get_db),
    _=Depends(require_permission("comprobantes.delete")),
):
    return service.eliminar_detalle(db, company_id, num_comprobante, detalle_id)
