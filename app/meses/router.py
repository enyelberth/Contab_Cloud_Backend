from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_permission
from app.database import get_db
from app.meses import schemas, service

router = APIRouter(prefix="/companies/{company_id}/meses", tags=["meses"])


@router.get(
    "/",
    response_model=List[schemas.Mes],
    summary="Listar meses de trabajo de una empresa",
)
def listar_meses(
    company_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("meses.view")),
):
    return service.get_meses(db, company_id)


@router.post(
    "/",
    response_model=schemas.Mes,
    status_code=201,
    summary="Crear un mes de trabajo",
)
def crear_mes(
    company_id: str,
    data: schemas.MesCreate,
    db=Depends(get_db),
    _=Depends(require_permission("meses.create")),
):
    return service.crear_mes(db, company_id, data)


@router.get(
    "/{mes_id}",
    response_model=schemas.Mes,
    summary="Obtener un mes de trabajo por id",
)
def obtener_mes(
    company_id: str,
    mes_id: int,
    db=Depends(get_db),
    _=Depends(require_permission("meses.view")),
):
    return service.get_mes(db, company_id, mes_id)


@router.put(
    "/{mes_id}",
    response_model=schemas.Mes,
    summary="Actualizar un mes de trabajo (solo los campos enviados)",
)
def actualizar_mes(
    company_id: str,
    mes_id: int,
    data: schemas.MesUpdate,
    db=Depends(get_db),
    _=Depends(require_permission("meses.edit")),
):
    return service.actualizar_mes(db, company_id, mes_id, data)


@router.delete(
    "/{mes_id}",
    summary="Eliminar un mes de trabajo",
)
def eliminar_mes(
    company_id: str,
    mes_id: int,
    db=Depends(get_db),
    _=Depends(require_permission("meses.delete")),
):
    return service.eliminar_mes(db, company_id, mes_id)
