from fastapi import HTTPException

from app.database import execute, fetch_all, fetch_one


def _get_product(db, tenant_id: str, product_id: str):
    return fetch_one(
        db,
        """
        SELECT uuid::text AS id,
               tenant_id::text AS tenant_id,
               sku,
               name,
               description,
               unit_price,
               cost_price,
               is_active,
               created_at,
               updated_at
        FROM inventory.products
        WHERE tenant_id = %s::uuid
          AND uuid = %s::uuid
          AND deleted_at IS NULL
        """,
        (tenant_id, product_id),
    )


def create_product(db, tenant_id: str, data):
    existing = fetch_one(
        db,
        """
        SELECT uuid
        FROM inventory.products
        WHERE tenant_id = %s::uuid
          AND sku = %s
          AND deleted_at IS NULL
        """,
        (tenant_id, data.sku),
    )
    if existing:
        raise HTTPException(status_code=400, detail="Product sku already exists")

    return execute(
        db,
        """
        INSERT INTO inventory.products (
            tenant_id,
            sku,
            name,
            description,
            unit_price,
            cost_price,
            is_active
        )
        VALUES (%s::uuid, %s, %s, %s, %s, %s, %s)
        RETURNING uuid::text AS id,
                  tenant_id::text AS tenant_id,
                  sku,
                  name,
                  description,
                  unit_price,
                  cost_price,
                  is_active,
                  created_at,
                  updated_at
        """,
        (
            tenant_id,
            data.sku,
            data.name,
            data.description,
            data.unit_price,
            data.cost_price,
            data.is_active,
        ),
        returning=True,
    )


def list_products(db, tenant_id: str, skip: int = 0, limit: int = 100):
    return fetch_all(
        db,
        """
        SELECT uuid::text AS id,
               tenant_id::text AS tenant_id,
               sku,
               name,
               description,
               unit_price,
               cost_price,
               is_active,
               created_at,
               updated_at
        FROM inventory.products
        WHERE tenant_id = %s::uuid
          AND deleted_at IS NULL
        ORDER BY created_at DESC
        OFFSET %s LIMIT %s
        """,
        (tenant_id, skip, limit),
    )


def get_product(db, tenant_id: str, product_id: str):
    product = _get_product(db, tenant_id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def update_product(db, tenant_id: str, product_id: str, data):
    current = get_product(db, tenant_id, product_id)
    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return current

    sku = payload.get("sku")
    if sku and sku != current["sku"]:
        existing = fetch_one(
            db,
            """
            SELECT uuid
            FROM inventory.products
            WHERE tenant_id = %s::uuid
              AND sku = %s
              AND uuid <> %s::uuid
              AND deleted_at IS NULL
            """,
            (tenant_id, sku, product_id),
        )
        if existing:
            raise HTTPException(status_code=400, detail="Product sku already exists")

    updated = execute(
        db,
        """
        UPDATE inventory.products
        SET sku = COALESCE(%s, sku),
            name = COALESCE(%s, name),
            description = COALESCE(%s, description),
            unit_price = COALESCE(%s, unit_price),
            cost_price = COALESCE(%s, cost_price),
            is_active = COALESCE(%s, is_active),
            updated_at = NOW()
        WHERE tenant_id = %s::uuid
          AND uuid = %s::uuid
          AND deleted_at IS NULL
        RETURNING uuid::text AS id,
                  tenant_id::text AS tenant_id,
                  sku,
                  name,
                  description,
                  unit_price,
                  cost_price,
                  is_active,
                  created_at,
                  updated_at
        """,
        (
            payload.get("sku"),
            payload.get("name"),
            payload.get("description"),
            payload.get("unit_price"),
            payload.get("cost_price"),
            payload.get("is_active"),
            tenant_id,
            product_id,
        ),
        returning=True,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated


def delete_product(db, tenant_id: str, product_id: str):
    row = execute(
        db,
        """
        UPDATE inventory.products
        SET deleted_at = NOW(),
            is_active = FALSE,
            updated_at = NOW()
        WHERE tenant_id = %s::uuid
          AND uuid = %s::uuid
          AND deleted_at IS NULL
        RETURNING uuid::text AS id
        """,
        (tenant_id, product_id),
        returning=True,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"detail": "Product deleted successfully"}
