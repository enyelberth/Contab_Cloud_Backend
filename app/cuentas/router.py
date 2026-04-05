from typing import List, Literal

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_permission
from app.database import get_db
from app.cuentas import schemas, service

router = APIRouter(prefix="/companies/{company_id}/cuentas", tags=["cuentas"])


# ==================================================================
# Rutas especiales (sin {txt_cuenta}, deben ir ANTES)
# ==================================================================

@router.get(
    "/comparar",
    response_model=schemas.ComparacionCuentas,
    summary="Comparar plan de cuentas entre 2 empresas",
    description=(
        "Muestra qué cuentas existen solo en el origen, solo en el destino, "
        "o en ambas. Útil para detectar diferencias antes de importar."
    ),
)
def comparar_cuentas(
    company_id: str,
    destino: str = Query(..., description="UUID de la empresa destino"),
    db=Depends(get_db),
    _=Depends(require_permission("cuentas.view")),
):
    return service.comparar_cuentas(db, company_id, destino)


@router.post(
    "/importar",
    response_model=schemas.ImportarResultado,
    summary="Importar plan de cuentas de una empresa a otra",
    description=(
        "Copia todas las cuentas del schema origen al schema destino. "
        "**modo=omitir** deja intactas las cuentas ya existentes en destino. "
        "**modo=reemplazar** sobreescribe las cuentas que coincidan por código."
    ),
)
def importar_cuentas(
    company_id: str,
    destino: str = Query(..., description="UUID de la empresa destino"),
    modo: Literal["omitir", "reemplazar"] = Query(
        "omitir", description="Qué hacer con cuentas que ya existen en destino"
    ),
    db=Depends(get_db),
    _=Depends(require_permission("cuentas.import")),
):
    return service.importar_cuentas(db, company_id, destino, modo)


@router.post(
    "/lote",
    response_model=schemas.LoteResultado,
    status_code=201,
    summary="Crear múltiples cuentas en una sola llamada",
    description=(
        "Inserta una lista de cuentas de forma masiva. "
        "Las que ya existan (mismo txt_cuenta) se omiten sin generar error."
    ),
)
def crear_cuentas_lote(
    company_id: str,
    cuentas: List[schemas.CuentaCreate],
    db=Depends(get_db),
    _=Depends(require_permission("cuentas.create")),
):
    return service.crear_cuentas_lote(db, company_id, cuentas)


# ==================================================================
# CRUD estándar
# ==================================================================

@router.get(
    "/",
    response_model=List[schemas.Cuenta],
    summary="Listar plan de cuentas de una empresa",
)
def listar_cuentas(
    company_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("cuentas.view")),
):
    return service.get_cuentas(db, company_id)


@router.post(
    "/",
    response_model=schemas.Cuenta,
    status_code=201,
    summary="Crear una cuenta en el plan de cuentas",
)
def crear_cuenta(
    company_id: str,
    data: schemas.CuentaCreate,
    db=Depends(get_db),
    _=Depends(require_permission("cuentas.create")),
):
    return service.crear_cuenta(db, company_id, data)


@router.get(
    "/{txt_cuenta}",
    response_model=schemas.Cuenta,
    summary="Obtener una cuenta por su código",
)
def obtener_cuenta(
    company_id: str,
    txt_cuenta: str,
    db=Depends(get_db),
    _=Depends(require_permission("cuentas.view")),
):
    return service.get_cuenta(db, company_id, txt_cuenta)


@router.put(
    "/{txt_cuenta}",
    response_model=schemas.Cuenta,
    summary="Actualizar una cuenta (solo los campos enviados)",
)
def actualizar_cuenta(
    company_id: str,
    txt_cuenta: str,
    data: schemas.CuentaUpdate,
    db=Depends(get_db),
    _=Depends(require_permission("cuentas.edit")),
):
    return service.actualizar_cuenta(db, company_id, txt_cuenta, data)


@router.delete(
    "/{txt_cuenta}",
    summary="Eliminar una cuenta del plan de cuentas",
)
def eliminar_cuenta(
    company_id: str,
    txt_cuenta: str,
    db=Depends(get_db),
    _=Depends(require_permission("cuentas.delete")),
):
    return service.eliminar_cuenta(db, company_id, txt_cuenta)
