from fastapi import HTTPException
from psycopg2 import sql

from app.audit import log_audit
from app.branche import schemas
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


def _row(schema: str, row: dict) -> dict:
    return {
        "id": str(row["uuid"]),
        "tenant_id": str(row["tenant_id"]),
        "name": row["name"],
        "address": row.get("address"),
        "phone": row.get("phone"),
        "is_active": row["is_active"],
        "created_at": row["created_at"],
    }


def get_branches(db, tenant_id: str, skip: int = 0, limit: int = 100):
    schema = _get_schema(db, tenant_id)
    query = sql.SQL(
        "SELECT uuid, tenant_id, name, address, phone, is_active, created_at "
        "FROM {}.branches WHERE is_active IS NOT NULL "
        "ORDER BY created_at ASC OFFSET %s LIMIT %s"
    ).format(sql.Identifier(schema))
    rows = fetch_all(db, query, (skip, limit))
    return [_row(schema, r) for r in rows]


def get_branch(db, tenant_id: str, branch_id: str):
    schema = _get_schema(db, tenant_id)
    query = sql.SQL(
        "SELECT uuid, tenant_id, name, address, phone, is_active, created_at "
        "FROM {}.branches WHERE uuid = %s::uuid"
    ).format(sql.Identifier(schema))
    row = fetch_one(db, query, (branch_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return _row(schema, row)


def create_branch(db, tenant_id: str, data: schemas.BranchCreate, actor_user_id: str):
    schema = _get_schema(db, tenant_id)
    query = sql.SQL(
        "INSERT INTO {}.branches (tenant_id, name, address, phone, is_active) "
        "VALUES (%s::uuid, %s, %s, %s, %s) "
        "RETURNING uuid, tenant_id, name, address, phone, is_active, created_at"
    ).format(sql.Identifier(schema))
    row = fetch_one(db, query, (tenant_id, data.name, data.address, data.phone, data.is_active))
    db.commit()
    result = _row(schema, row)
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="branches",
        action="CREATE",
        entity_type="branches",
        entity_id=result["id"],
        after_data=result,
    )
    return result


def update_branch(db, tenant_id: str, branch_id: str, data: schemas.BranchUpdate, actor_user_id: str):
    before = get_branch(db, tenant_id, branch_id)
    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return before

    schema = _get_schema(db, tenant_id)
    query = sql.SQL(
        "UPDATE {}.branches "
        "SET name = COALESCE(%s, name), address = COALESCE(%s, address), "
        "    phone = COALESCE(%s, phone), is_active = COALESCE(%s, is_active), "
        "    updated_at = NOW() "
        "WHERE uuid = %s::uuid "
        "RETURNING uuid, tenant_id, name, address, phone, is_active, created_at"
    ).format(sql.Identifier(schema))
    row = fetch_one(
        db, query,
        (payload.get("name"), payload.get("address"), payload.get("phone"),
         payload.get("is_active"), branch_id),
    )
    db.commit()
    result = _row(schema, row)
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="branches",
        action="UPDATE",
        entity_type="branches",
        entity_id=branch_id,
        before_data=before,
        after_data=result,
    )
    return result


def delete_branch(db, tenant_id: str, branch_id: str, actor_user_id: str):
    before = get_branch(db, tenant_id, branch_id)
    schema = _get_schema(db, tenant_id)
    query = sql.SQL(
        "UPDATE {}.branches SET is_active = FALSE, updated_at = NOW() "
        "WHERE uuid = %s::uuid RETURNING uuid"
    ).format(sql.Identifier(schema))
    fetch_one(db, query, (branch_id,))
    db.commit()
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="branches",
        action="DELETE",
        entity_type="branches",
        entity_id=branch_id,
        before_data=before,
    )
    return {"detail": "Sucursal desactivada correctamente"}
