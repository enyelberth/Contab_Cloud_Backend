from typing import List

from fastapi import APIRouter, Depends

from app.database import get_db
from app.prueba import schemas, service

router = APIRouter(prefix="/prueba", tags=["prueba"])


@router.get(
    "/{company_id}",
    response_model=List[schemas.Prueba],
    summary="Listar registros de prueba de una empresa",
    description=(
        "Devuelve los registros de la tabla `prueba` del schema "
        "correspondiente a la empresa indicada (empresa_1, empresa_2, …)."
    ),
)
def listar_prueba(company_id: int, db=Depends(get_db)):
    return service.get_prueba(db, company_id)


@router.post(
    "/{company_id}",
    response_model=schemas.Prueba,
    status_code=201,
    summary="Crear registro de prueba en una empresa",
    description="Inserta un registro en la tabla `prueba` del schema de la empresa indicada.",
)
def crear_prueba(company_id: int, data: schemas.PruebaCreate, db=Depends(get_db)):
    return service.crear_prueba(db, company_id, data)
