from fastapi import HTTPException
from psycopg2 import sql

from app.audit import log_audit
from app.database import execute, fetch_all, fetch_one


def _get_schema(db, tenant_id: str) -> str:
    row = fetch_one(
        db,
        "SELECT schema_name FROM global.tenants WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (tenant_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return row["schema_name"]


def _fmt(row: dict) -> dict:
    return {
        "id": str(row["uuid"]),
        "tenant_id": str(row["tenant_id"]),
        "sku": row["sku"],
        "name": row["name"],
        "description": row.get("description"),
        "unit_price": float(row.get("unit_price") or 0),
        "cost_price": float(row.get("cost_price") or 0),
        "is_active": row["is_active"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _get_product_row(db, schema: str, tenant_id: str, product_id: str):
    q = sql.SQL(
        "SELECT uuid, tenant_id, sku, name, description, unit_price, cost_price, "
        "is_active, created_at, updated_at "
        "FROM {}.products "
        "WHERE uuid = %s::uuid AND tenant_id = %s::uuid AND deleted_at IS NULL"
    ).format(sql.Identifier(schema))
    return fetch_one(db, q, (product_id, tenant_id))


def create_product(db, tenant_id: str, data, actor_user_id: str | None = None):
    schema = _get_schema(db, tenant_id)

    dup_q = sql.SQL(
        "SELECT uuid FROM {}.products WHERE sku = %s AND tenant_id = %s::uuid AND deleted_at IS NULL"
    ).format(sql.Identifier(schema))
    if fetch_one(db, dup_q, (data.sku, tenant_id)):
        raise HTTPException(status_code=400, detail="El SKU ya existe en esta empresa")

    q = sql.SQL(
        "INSERT INTO {}.products (tenant_id, sku, name, description, unit_price, cost_price, is_active) "
        "VALUES (%s::uuid, %s, %s, %s, %s, %s, %s) "
        "RETURNING uuid, tenant_id, sku, name, description, unit_price, cost_price, is_active, created_at, updated_at"
    ).format(sql.Identifier(schema))
    row = fetch_one(db, q, (tenant_id, data.sku, data.name, data.description,
                            data.unit_price, data.cost_price, data.is_active))
    db.commit()
    result = _fmt(row)
    if actor_user_id:
        log_audit(db, actor_user_id=actor_user_id, company_id=tenant_id,
                  module="products", action="CREATE", entity_type="products",
                  entity_id=result["id"], after_data=result)
    return result


def list_products(db, tenant_id: str, skip: int = 0, limit: int = 100):
    schema = _get_schema(db, tenant_id)
    q = sql.SQL(
        "SELECT uuid, tenant_id, sku, name, description, unit_price, cost_price, "
        "is_active, created_at, updated_at "
        "FROM {}.products "
        "WHERE tenant_id = %s::uuid AND deleted_at IS NULL "
        "ORDER BY created_at DESC OFFSET %s LIMIT %s"
    ).format(sql.Identifier(schema))
    rows = fetch_all(db, q, (tenant_id, skip, limit))
    return [_fmt(r) for r in rows]


def get_product(db, tenant_id: str, product_id: str):
    schema = _get_schema(db, tenant_id)
    row = _get_product_row(db, schema, tenant_id, product_id)
    if not row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _fmt(row)


def update_product(db, tenant_id: str, product_id: str, data, actor_user_id: str | None = None):
    schema = _get_schema(db, tenant_id)
    current_row = _get_product_row(db, schema, tenant_id, product_id)
    if not current_row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return _fmt(current_row)

    sku = payload.get("sku")
    if sku and sku != current_row["sku"]:
        dup_q = sql.SQL(
            "SELECT uuid FROM {}.products WHERE sku = %s AND tenant_id = %s::uuid "
            "AND uuid <> %s::uuid AND deleted_at IS NULL"
        ).format(sql.Identifier(schema))
        if fetch_one(db, dup_q, (sku, tenant_id, product_id)):
            raise HTTPException(status_code=400, detail="El SKU ya existe en esta empresa")

    q = sql.SQL(
        "UPDATE {}.products "
        "SET sku = COALESCE(%s, sku), name = COALESCE(%s, name), "
        "    description = COALESCE(%s, description), "
        "    unit_price = COALESCE(%s, unit_price), cost_price = COALESCE(%s, cost_price), "
        "    is_active = COALESCE(%s, is_active), updated_at = NOW() "
        "WHERE uuid = %s::uuid AND tenant_id = %s::uuid AND deleted_at IS NULL "
        "RETURNING uuid, tenant_id, sku, name, description, unit_price, cost_price, "
        "          is_active, created_at, updated_at"
    ).format(sql.Identifier(schema))
    row = fetch_one(db, q, (
        payload.get("sku"), payload.get("name"), payload.get("description"),
        payload.get("unit_price"), payload.get("cost_price"), payload.get("is_active"),
        product_id, tenant_id,
    ))
    db.commit()
    result = _fmt(row)
    if actor_user_id:
        log_audit(db, actor_user_id=actor_user_id, company_id=tenant_id,
                  module="products", action="UPDATE", entity_type="products",
                  entity_id=product_id, before_data=_fmt(current_row), after_data=result)
    return result


def delete_product(db, tenant_id: str, product_id: str, actor_user_id: str | None = None):
    schema = _get_schema(db, tenant_id)
    q = sql.SQL(
        "UPDATE {}.products SET deleted_at = NOW(), is_active = FALSE, updated_at = NOW() "
        "WHERE uuid = %s::uuid AND tenant_id = %s::uuid AND deleted_at IS NULL "
        "RETURNING uuid"
    ).format(sql.Identifier(schema))
    row = fetch_one(db, q, (product_id, tenant_id))
    db.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if actor_user_id:
        log_audit(db, actor_user_id=actor_user_id, company_id=tenant_id,
                  module="products", action="DELETE", entity_type="products",
                  entity_id=product_id)
    return {"detail": "Producto eliminado correctamente"}
