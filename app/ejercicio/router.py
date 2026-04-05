from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_permission
from app.database import get_db
from app.ejercicio import schemas, service

router = APIRouter(prefix="/companies/{company_id}/ejercicios", tags=["ejercicios"])


@router.get(
    "/",
    response_model=List[schemas.Ejercicio],
    summary="Listar ejercicios contables de una empresa",
)
def listar_ejercicios(
    company_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("ejercicios.view")),
):
    return service.get_ejercicios(db, company_id)


@router.post(
    "/",
    response_model=schemas.EjercicioCreado,
    status_code=201,
    summary="Crear un ejercicio contable",
    description=(
        "Crea el ejercicio y genera automáticamente los 12 meses de trabajo "
        "con **Status=4** y **Bloqueo=1**. El usuario debe abrirlos manualmente."
    ),
)
def crear_ejercicio(
    company_id: str,
    data: schemas.EjercicioCreate,
    db=Depends(get_db),
    _=Depends(require_permission("ejercicios.create")),
):
    return service.crear_ejercicio(db, company_id, data)


@router.get(
    "/{ejercicio_id}",
    response_model=schemas.Ejercicio,
    summary="Obtener un ejercicio contable por id",
)
def obtener_ejercicio(
    company_id: str,
    ejercicio_id: int,
    db=Depends(get_db),
    _=Depends(require_permission("ejercicios.view")),
):
    return service.get_ejercicio(db, company_id, ejercicio_id)


@router.put(
    "/{ejercicio_id}",
    response_model=schemas.Ejercicio,
    summary="Actualizar un ejercicio contable",
)
def actualizar_ejercicio(
    company_id: str,
    ejercicio_id: int,
    data: schemas.EjercicioUpdate,
    db=Depends(get_db),
    _=Depends(require_permission("ejercicios.edit")),
):
    return service.actualizar_ejercicio(db, company_id, ejercicio_id, data)


@router.delete(
    "/{ejercicio_id}",
    summary="Eliminar un ejercicio contable",
)
def eliminar_ejercicio(
    company_id: str,
    ejercicio_id: int,
    db=Depends(get_db),
    _=Depends(require_permission("ejercicios.delete")),
):
    return service.eliminar_ejercicio(db, company_id, ejercicio_id)
