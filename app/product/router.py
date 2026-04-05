from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_permission
from app.database import get_db
from app.product import schemas, service

router = APIRouter(prefix="/companies/{company_id}/products", tags=["products"])


@router.get("/", response_model=List[schemas.ProductResponse])
def list_products(
    company_id: str,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db),
    _=Depends(require_permission("products.view")),
):
    return service.list_products(db, tenant_id=company_id, skip=skip, limit=limit)


@router.post("/", response_model=schemas.ProductResponse, status_code=201)
def create_product(
    company_id: str,
    body: schemas.ProductCreate,
    db=Depends(get_db),
    current_user=Depends(require_permission("products.create")),
):
    return service.create_product(db, tenant_id=company_id, data=body, actor_user_id=current_user["id"])


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
    body: schemas.ProductUpdate,
    db=Depends(get_db),
    current_user=Depends(require_permission("products.edit")),
):
    return service.update_product(db, tenant_id=company_id, product_id=product_id, data=body, actor_user_id=current_user["id"])


@router.delete("/{product_id}")
def delete_product(
    company_id: str,
    product_id: str,
    db=Depends(get_db),
    current_user=Depends(require_permission("products.delete")),
):
    return service.delete_product(db, tenant_id=company_id, product_id=product_id, actor_user_id=current_user["id"])
