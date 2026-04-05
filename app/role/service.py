from fastapi import HTTPException

from app.audit import log_audit
from app.database import execute, fetch_all, fetch_one
from app.role import schemas


def _fmt(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "description": row.get("description"),
        "level": row["level"],
        "is_system": row["is_system"],
    }


def get_roles(db, skip: int = 0, limit: int = 100):
    rows = fetch_all(
        db,
        """
        SELECT uuid::text AS id, name, description, level, is_system
        FROM global.roles
        WHERE deleted_at IS NULL
        ORDER BY level DESC, name ASC
        OFFSET %s LIMIT %s
        """,
        (skip, limit),
    )
    return [_fmt(r) for r in rows]


def get_role(db, role_id: str):
    row = fetch_one(
        db,
        "SELECT uuid::text AS id, name, description, level, is_system FROM global.roles WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (role_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return _fmt(row)


def create_role(db, data: schemas.RoleCreate, actor_user_id: str, tenant_id: str | None = None):
    existing = fetch_one(
        db,
        "SELECT uuid FROM global.roles WHERE name = %s AND deleted_at IS NULL",
        (data.name,),
    )
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")

    row = execute(
        db,
        """
        INSERT INTO global.roles (name, description, level, is_system)
        VALUES (%s, %s, %s, %s)
        RETURNING uuid::text AS id, name, description, level, is_system
        """,
        (data.name, data.description, data.level, data.is_system),
        returning=True,
    )
    result = _fmt(row)
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="roles",
        action="CREATE",
        entity_type="roles",
        entity_id=result["id"],
        after_data=result,
    )
    return result


def update_role(db, role_id: str, data: schemas.RoleUpdate, actor_user_id: str, tenant_id: str | None = None):
    before = get_role(db, role_id)

    if before["is_system"]:
        raise HTTPException(status_code=403, detail="Los roles de sistema no se pueden modificar")

    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return before

    if payload.get("name") and payload["name"] != before["name"]:
        dup = fetch_one(
            db,
            "SELECT uuid FROM global.roles WHERE name = %s AND uuid <> %s::uuid AND deleted_at IS NULL",
            (payload["name"], role_id),
        )
        if dup:
            raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")

    row = execute(
        db,
        """
        UPDATE global.roles
        SET name        = COALESCE(%s, name),
            description = COALESCE(%s, description),
            level       = COALESCE(%s, level)
        WHERE uuid = %s::uuid AND deleted_at IS NULL
        RETURNING uuid::text AS id, name, description, level, is_system
        """,
        (payload.get("name"), payload.get("description"), payload.get("level"), role_id),
        returning=True,
    )
    result = _fmt(row)
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="roles",
        action="UPDATE",
        entity_type="roles",
        entity_id=role_id,
        before_data=before,
        after_data=result,
    )
    return result


def delete_role(db, role_id: str, actor_user_id: str, tenant_id: str | None = None):
    role = get_role(db, role_id)

    if role["is_system"]:
        raise HTTPException(status_code=403, detail="Los roles de sistema no se pueden eliminar")

    execute(
        db,
        "UPDATE global.roles SET deleted_at = NOW() WHERE uuid = %s::uuid",
        (role_id,),
    )
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="roles",
        action="DELETE",
        entity_type="roles",
        entity_id=role_id,
        before_data=role,
    )
    return {"detail": "Rol eliminado correctamente"}
