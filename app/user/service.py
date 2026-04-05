from fastapi import HTTPException

from app.audit import log_audit
from app.auth.security import hash_password
from app.database import execute, fetch_all, fetch_one
from app.user import schemas


def _format_user(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "username": row["username"],
        "email": row["email"],
        "first_name": row.get("first_name"),
        "first_lastname": row.get("first_lastname"),
        "phone": row.get("phone"),
        "status": row["status"],
        "role_id": str(row["role_id"]) if row.get("role_id") else None,
        "role_name": row.get("role_name"),
        "tenant_id": str(row["tenant_id"]) if row.get("tenant_id") else None,
        "created_at": row["created_at"],
    }


def get_users(db, tenant_id: str, skip: int = 0, limit: int = 100):
    rows = fetch_all(
        db,
        """
        SELECT u.uuid::text AS id,
               u.username, u.email, u.status, u.created_at,
               p.first_name, p.first_lastname, p.phone,
               utr.role_id::text AS role_id, r.name AS role_name,
               ut.tenant_id::text AS tenant_id
        FROM global.users u
        INNER JOIN global.user_tenants ut
               ON ut.user_id = u.uuid AND ut.tenant_id = %s::uuid AND ut.is_active = TRUE
        LEFT JOIN global.profiles p ON p.user_id = u.uuid
        LEFT JOIN global.user_tenant_roles utr
               ON utr.user_id = u.uuid AND utr.tenant_id = ut.tenant_id AND utr.revoked_at IS NULL
        LEFT JOIN global.roles r ON r.uuid = utr.role_id
        WHERE u.deleted_at IS NULL
        ORDER BY u.created_at ASC
        OFFSET %s LIMIT %s
        """,
        (tenant_id, skip, limit),
    )
    return [_format_user(r) for r in rows]


def get_user(db, tenant_id: str, user_id: str):
    row = fetch_one(
        db,
        """
        SELECT u.uuid::text AS id,
               u.username, u.email, u.status, u.created_at,
               p.first_name, p.first_lastname, p.phone,
               utr.role_id::text AS role_id, r.name AS role_name,
               ut.tenant_id::text AS tenant_id
        FROM global.users u
        INNER JOIN global.user_tenants ut
               ON ut.user_id = u.uuid AND ut.tenant_id = %s::uuid AND ut.is_active = TRUE
        LEFT JOIN global.profiles p ON p.user_id = u.uuid
        LEFT JOIN global.user_tenant_roles utr
               ON utr.user_id = u.uuid AND utr.tenant_id = ut.tenant_id AND utr.revoked_at IS NULL
        LEFT JOIN global.roles r ON r.uuid = utr.role_id
        WHERE u.uuid = %s::uuid AND u.deleted_at IS NULL
        """,
        (tenant_id, user_id),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return _format_user(row)


def create_user(db, tenant_id: str, data: schemas.UserCreate, actor_user_id: str):
    existing = fetch_one(
        db,
        "SELECT uuid FROM global.users WHERE (email = %s OR username = %s) AND deleted_at IS NULL",
        (data.email, data.username),
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email o username ya existe")

    role = fetch_one(
        db,
        "SELECT uuid::text AS id FROM global.roles WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (data.role_id,),
    )
    if not role:
        raise HTTPException(status_code=400, detail="Rol no encontrado")

    tenant = fetch_one(
        db,
        "SELECT uuid FROM global.tenants WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (tenant_id,),
    )
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    user = execute(
        db,
        """
        INSERT INTO global.users (username, email, password_hash, status, email_verified_at)
        VALUES (%s, %s, %s, 'active', NOW())
        RETURNING uuid::text AS id, username, email, status, created_at
        """,
        (data.username, str(data.email), hash_password(data.password)),
        returning=True,
    )

    execute(
        db,
        """
        INSERT INTO global.profiles (user_id, first_name, first_lastname, phone)
        VALUES (%s::uuid, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
            SET first_name = EXCLUDED.first_name,
                first_lastname = EXCLUDED.first_lastname,
                phone = EXCLUDED.phone
        """,
        (user["id"], data.first_name, data.first_lastname, data.phone),
    )

    execute(
        db,
        """
        INSERT INTO global.user_tenants (user_id, tenant_id, is_active, invited_by, joined_at)
        VALUES (%s::uuid, %s::uuid, TRUE, %s::uuid, NOW())
        ON CONFLICT (user_id, tenant_id) DO UPDATE SET is_active = TRUE
        """,
        (user["id"], tenant_id, actor_user_id),
    )

    execute(
        db,
        """
        INSERT INTO global.user_tenant_roles (user_id, tenant_id, role_id, assigned_by)
        VALUES (%s::uuid, %s::uuid, %s::uuid, %s::uuid)
        ON CONFLICT DO NOTHING
        """,
        (user["id"], tenant_id, data.role_id, actor_user_id),
    )

    result = get_user(db, tenant_id, user["id"])
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="users",
        action="CREATE",
        entity_type="users",
        entity_id=user["id"],
        after_data={k: v for k, v in result.items() if k != "password_hash"},
    )
    return result


def update_user(db, tenant_id: str, user_id: str, data: schemas.UserUpdate, actor_user_id: str):
    before = get_user(db, tenant_id, user_id)
    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return before

    password_hash = hash_password(payload.pop("password")) if payload.get("password") else None

    execute(
        db,
        """
        UPDATE global.users
        SET username   = COALESCE(%s, username),
            email      = COALESCE(%s, email),
            password_hash = COALESCE(%s, password_hash),
            status     = COALESCE(%s, status),
            updated_at = NOW()
        WHERE uuid = %s::uuid AND deleted_at IS NULL
        """,
        (
            payload.get("username"),
            str(payload["email"]) if payload.get("email") else None,
            password_hash,
            payload.get("status"),
            user_id,
        ),
    )

    execute(
        db,
        """
        UPDATE global.profiles
        SET first_name     = COALESCE(%s, first_name),
            first_lastname = COALESCE(%s, first_lastname),
            phone          = COALESCE(%s, phone),
            updated_at     = NOW()
        WHERE user_id = %s::uuid
        """,
        (payload.get("first_name"), payload.get("first_lastname"), payload.get("phone"), user_id),
    )

    result = get_user(db, tenant_id, user_id)
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="users",
        action="UPDATE",
        entity_type="users",
        entity_id=user_id,
        before_data=before,
        after_data=result,
    )
    return result


def delete_user(db, tenant_id: str, user_id: str, actor_user_id: str):
    before = get_user(db, tenant_id, user_id)

    execute(
        db,
        "UPDATE global.users SET deleted_at = NOW(), status = 'inactive', updated_at = NOW() WHERE uuid = %s::uuid",
        (user_id,),
    )
    execute(
        db,
        "UPDATE global.user_tenants SET is_active = FALSE WHERE user_id = %s::uuid AND tenant_id = %s::uuid",
        (user_id, tenant_id),
    )
    execute(
        db,
        "UPDATE global.user_tenant_roles SET revoked_at = NOW(), revoked_by = %s::uuid WHERE user_id = %s::uuid AND tenant_id = %s::uuid AND revoked_at IS NULL",
        (actor_user_id, user_id, tenant_id),
    )

    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="users",
        action="DELETE",
        entity_type="users",
        entity_id=user_id,
        before_data=before,
    )
    return {"detail": "Usuario eliminado correctamente"}
