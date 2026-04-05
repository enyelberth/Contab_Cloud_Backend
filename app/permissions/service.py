from fastapi import HTTPException

from app.audit import log_audit
from app.database import execute, fetch_all, fetch_one
from app.permissions import schemas


def get_permissions(db, skip: int = 0, limit: int = 100):
    return fetch_all(
        db,
        """
        SELECT uuid::text AS id, module, name, slug, description
        FROM global.permissions
        ORDER BY module ASC, name ASC
        OFFSET %s LIMIT %s
        """,
        (skip, limit),
    )


def get_permission(db, permission_id: str):
    row = fetch_one(
        db,
        "SELECT uuid::text AS id, module, name, slug, description FROM global.permissions WHERE uuid = %s::uuid",
        (permission_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Permiso no encontrado")
    return row


def create_permission(db, data: schemas.PermissionCreate, actor_user_id: str, tenant_id: str | None = None):
    existing = fetch_one(
        db,
        "SELECT uuid FROM global.permissions WHERE slug = %s",
        (data.slug,),
    )
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un permiso con ese slug")

    row = execute(
        db,
        """
        INSERT INTO global.permissions (module, name, slug, description)
        VALUES (%s, %s, %s, %s)
        RETURNING uuid::text AS id, module, name, slug, description
        """,
        (data.module, data.name, data.slug, data.description),
        returning=True,
    )
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="permissions",
        action="CREATE",
        entity_type="permissions",
        entity_id=row["id"],
        after_data=dict(row),
    )
    return row


def delete_permission(db, permission_id: str, actor_user_id: str, tenant_id: str | None = None):
    perm = get_permission(db, permission_id)
    execute(
        db,
        "DELETE FROM global.role_permissions WHERE permission_id = %s::uuid",
        (permission_id,),
    )
    execute(
        db,
        "DELETE FROM global.permissions WHERE uuid = %s::uuid",
        (permission_id,),
    )
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="permissions",
        action="DELETE",
        entity_type="permissions",
        entity_id=permission_id,
        before_data=dict(perm),
    )
    return {"detail": "Permiso eliminado correctamente"}


def assign_permissions_to_role(db, data: schemas.PermissionAssign, actor_user_id: str, tenant_id: str | None = None):
    role = fetch_one(
        db,
        "SELECT uuid::text AS id, name FROM global.roles WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (data.role_id,),
    )
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    found = fetch_all(
        db,
        "SELECT uuid::text AS id FROM global.permissions WHERE uuid = ANY(%s::uuid[])",
        (data.permission_ids,),
    )
    if len(found) != len(set(data.permission_ids)):
        raise HTTPException(status_code=400, detail="Uno o más permisos no existen")

    # Reemplazar permisos del rol
    execute(
        db,
        "DELETE FROM global.role_permissions WHERE role_id = %s::uuid",
        (data.role_id,),
    )
    with db.cursor() as cur:
        cur.executemany(
            "INSERT INTO global.role_permissions (role_id, permission_id) VALUES (%s::uuid, %s::uuid) ON CONFLICT DO NOTHING",
            [(data.role_id, pid) for pid in data.permission_ids],
        )
    db.commit()

    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="permissions",
        action="ASSIGN",
        entity_type="roles",
        entity_id=data.role_id,
        after_data={"permission_ids": data.permission_ids},
    )

    perms = fetch_all(
        db,
        """
        SELECT p.uuid::text AS id, p.module, p.name, p.slug, p.description
        FROM global.role_permissions rp
        INNER JOIN global.permissions p ON p.uuid = rp.permission_id
        WHERE rp.role_id = %s::uuid
        ORDER BY p.module, p.name
        """,
        (data.role_id,),
    )
    return {"role_id": role["id"], "role_name": role["name"], "permissions": perms}


def get_role_permissions(db, role_id: str):
    role = fetch_one(
        db,
        "SELECT uuid::text AS id, name FROM global.roles WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (role_id,),
    )
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    perms = fetch_all(
        db,
        """
        SELECT p.uuid::text AS id, p.module, p.name, p.slug, p.description
        FROM global.role_permissions rp
        INNER JOIN global.permissions p ON p.uuid = rp.permission_id
        WHERE rp.role_id = %s::uuid
        ORDER BY p.module, p.name
        """,
        (role_id,),
    )
    return {"role_id": role["id"], "role_name": role["name"], "permissions": perms}
