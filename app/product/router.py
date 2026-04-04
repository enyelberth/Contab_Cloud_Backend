from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_permission
from app.database import get_db
from app.product import schemas, service

router = APIRouter(prefix="/companies/{company_id}/products", tags=["products"])


@router.post("/", response_model=schemas.ProductResponse)
def create_product(
    company_id: str,
    payload: schemas.ProductCreate,
    db=Depends(get_db),
    _=Depends(require_permission("products.create")),
):
    return service.create_product(db, tenant_id=company_id, data=payload)


@router.get("/", response_model=List[schemas.ProductResponse])
def list_products(
    company_id: str,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db),
    _=Depends(require_permission("products.view")),
):
    return service.list_products(db, tenant_id=company_id, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(
    company_id: str,
    product_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("products.view")),
):
    return service.get_product(db, tenant_id=company_id, product_id=product_id)


@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    company_id: str,
    product_id: str,
    payload: schemas.ProductUpdate,
    db=Depends(get_db),
    _=Depends(require_permission("products.update")),
):
    return service.update_product(db, tenant_id=company_id, product_id=product_id, data=payload)


@router.delete("/{product_id}")
def delete_product(
    company_id: str,
    product_id: str,
    db=Depends(get_db),
    _=Depends(require_permission("products.delete")),
):
    return service.delete_product(db, tenant_id=company_id, product_id=product_id)
