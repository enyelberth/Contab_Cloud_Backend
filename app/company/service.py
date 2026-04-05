from fastapi import HTTPException

from app.audit import log_audit
from app.company import schemas
from app.database import execute, execute_script, fetch_all, fetch_one


def _get_tenant_by_id(db, tenant_id: str):
    return fetch_one(
        db,
        """
        SELECT uuid::text AS id, name, slug, rif, address, location, phone, email,
               status, plan, schema_name, created_at
        FROM global.tenants
        WHERE uuid = %s::uuid AND deleted_at IS NULL
        """,
        (tenant_id,),
    )


def create_tenant(db, data: schemas.TenantCreate, created_by: str):
    existing = fetch_one(
        db,
        "SELECT uuid FROM global.tenants WHERE slug = %s AND deleted_at IS NULL",
        (data.slug,),
    )
    if existing:
        raise HTTPException(status_code=400, detail="El slug ya está en uso")

    if data.rif:
        dup = fetch_one(
            db,
            "SELECT uuid FROM global.tenants WHERE rif = %s AND deleted_at IS NULL",
            (data.rif,),
        )
        if dup:
            raise HTTPException(status_code=400, detail="El RIF ya está registrado")

    tenant = execute(
        db,
        """
        INSERT INTO global.tenants (name, slug, rif, address, location, phone, email, status, plan)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', %s)
        RETURNING uuid::text AS id, name, slug, rif, address, location, phone, email,
                  status, plan, schema_name, created_at
        """,
        (
            data.name,
            data.slug,
            data.rif,
            data.address,
            data.location,
            data.phone,
            str(data.email) if data.email else None,
            data.plan,
        ),
        returning=True,
    )

    # Crear schema del tenant con todas sus tablas
    with db.cursor() as cur:
        cur.execute("CALL global.sp_create_tenant_schema(%s)", (data.slug,))
    db.commit()

    # Vincular el creador como tenant_admin
    tenant_admin_role = fetch_one(
        db,
        "SELECT uuid::text AS id FROM global.roles WHERE name = 'tenant_admin' AND deleted_at IS NULL",
    )
    if not tenant_admin_role:
        raise HTTPException(status_code=500, detail="Rol tenant_admin no encontrado")

    # user_tenants
    execute(
        db,
        """
        INSERT INTO global.user_tenants (user_id, tenant_id, is_active, invited_by, joined_at)
        VALUES (%s::uuid, %s::uuid, TRUE, %s::uuid, NOW())
        ON CONFLICT (user_id, tenant_id) DO UPDATE SET is_active = TRUE, joined_at = NOW()
        """,
        (created_by, tenant["id"], created_by),
    )

    # user_tenant_roles
    execute(
        db,
        """
        INSERT INTO global.user_tenant_roles (user_id, tenant_id, role_id, assigned_by)
        VALUES (%s::uuid, %s::uuid, %s::uuid, %s::uuid)
        ON CONFLICT DO NOTHING
        """,
        (created_by, tenant["id"], tenant_admin_role["id"], created_by),
    )

    log_audit(
        db,
        actor_user_id=created_by,
        company_id=tenant["id"],
        module="companies",
        action="CREATE",
        entity_type="tenants",
        entity_id=tenant["id"],
        after_data=dict(tenant),
    )

    return tenant


def get_tenants(db, skip: int = 0, limit: int = 100, user_id: str | None = None):
    if user_id is None:
        return fetch_all(
            db,
            """
            SELECT uuid::text AS id, name, slug, rif, address, location, phone, email,
                   status, plan, schema_name, created_at
            FROM global.tenants
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            OFFSET %s LIMIT %s
            """,
            (skip, limit),
        )

    return fetch_all(
        db,
        """
        SELECT t.uuid::text AS id, t.name, t.slug, t.rif, t.address, t.location,
               t.phone, t.email, t.status, t.plan, t.schema_name, t.created_at
        FROM global.tenants t
        INNER JOIN global.user_tenants ut ON ut.tenant_id = t.uuid
        WHERE ut.user_id = %s::uuid
          AND ut.is_active = TRUE
          AND t.deleted_at IS NULL
        ORDER BY t.created_at DESC
        OFFSET %s LIMIT %s
        """,
        (user_id, skip, limit),
    )


def get_tenant(db, tenant_id: str):
    tenant = _get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return tenant


def update_tenant(db, tenant_id: str, data: schemas.TenantUpdate, actor_user_id: str):
    tenant = get_tenant(db, tenant_id)
    payload = data.model_dump(exclude_unset=True)
    if not payload:
        return tenant

    updated = execute(
        db,
        """
        UPDATE global.tenants
        SET name      = COALESCE(%s, name),
            rif       = COALESCE(%s, rif),
            address   = COALESCE(%s, address),
            location  = COALESCE(%s, location),
            phone     = COALESCE(%s, phone),
            email     = COALESCE(%s, email),
            plan      = COALESCE(%s, plan),
            updated_at = NOW()
        WHERE uuid = %s::uuid AND deleted_at IS NULL
        RETURNING uuid::text AS id, name, slug, rif, address, location, phone, email,
                  status, plan, schema_name, created_at
        """,
        (
            payload.get("name"),
            payload.get("rif"),
            payload.get("address"),
            payload.get("location"),
            payload.get("phone"),
            str(payload["email"]) if payload.get("email") else None,
            payload.get("plan"),
            tenant_id,
        ),
        returning=True,
    )

    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="companies",
        action="UPDATE",
        entity_type="tenants",
        entity_id=tenant_id,
        before_data=dict(tenant),
        after_data=dict(updated),
    )
    return updated


def delete_tenant(db, tenant_id: str, actor_user_id: str):
    tenant = get_tenant(db, tenant_id)

    execute(
        db,
        "UPDATE global.tenants SET deleted_at = NOW(), status = 'cancelled' WHERE uuid = %s::uuid",
        (tenant_id,),
    )
    execute(
        db,
        "UPDATE global.user_tenants SET is_active = FALSE WHERE tenant_id = %s::uuid",
        (tenant_id,),
    )

    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="companies",
        action="DELETE",
        entity_type="tenants",
        entity_id=tenant_id,
        before_data=dict(tenant),
    )
    return {"detail": "Empresa eliminada correctamente"}


def get_members(db, tenant_id: str):
    get_tenant(db, tenant_id)
    return fetch_all(
        db,
        """
        SELECT u.uuid::text AS user_id,
               ut.tenant_id::text AS tenant_id,
               utr.role_id::text AS role_id,
               r.name AS role_name,
               u.username,
               u.email,
               p.first_name,
               p.first_lastname,
               ut.is_active,
               ut.joined_at
        FROM global.user_tenants ut
        INNER JOIN global.users u ON u.uuid = ut.user_id
        LEFT JOIN global.profiles p ON p.user_id = ut.user_id
        LEFT JOIN global.user_tenant_roles utr
               ON utr.user_id = ut.user_id
              AND utr.tenant_id = ut.tenant_id
              AND utr.revoked_at IS NULL
        LEFT JOIN global.roles r ON r.uuid = utr.role_id
        WHERE ut.tenant_id = %s::uuid
          AND u.deleted_at IS NULL
        ORDER BY ut.joined_at ASC
        """,
        (tenant_id,),
    )


def add_member(db, tenant_id: str, data: schemas.TenantMemberCreate, invited_by: str):
    get_tenant(db, tenant_id)

    user = fetch_one(
        db,
        "SELECT uuid::text AS id FROM global.users WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (data.user_id,),
    )
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    role = fetch_one(
        db,
        "SELECT uuid::text AS id FROM global.roles WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (data.role_id,),
    )
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    execute(
        db,
        """
        INSERT INTO global.user_tenants (user_id, tenant_id, is_active, invited_by, joined_at)
        VALUES (%s::uuid, %s::uuid, TRUE, %s::uuid, NOW())
        ON CONFLICT (user_id, tenant_id) DO UPDATE SET is_active = TRUE
        """,
        (data.user_id, tenant_id, invited_by),
    )

    execute(
        db,
        """
        INSERT INTO global.user_tenant_roles (user_id, tenant_id, role_id, assigned_by)
        VALUES (%s::uuid, %s::uuid, %s::uuid, %s::uuid)
        ON CONFLICT DO NOTHING
        """,
        (data.user_id, tenant_id, data.role_id, invited_by),
    )

    log_audit(
        db,
        actor_user_id=invited_by,
        company_id=tenant_id,
        module="companies",
        action="CREATE",
        entity_type="user_tenants",
        entity_id=data.user_id,
        after_data={"user_id": data.user_id, "role_id": data.role_id},
    )

    members = get_members(db, tenant_id)
    return next((m for m in members if m["user_id"] == data.user_id), None)


def remove_member(db, tenant_id: str, user_id: str, actor_user_id: str):
    get_tenant(db, tenant_id)

    membership = fetch_one(
        db,
        "SELECT uuid FROM global.user_tenants WHERE tenant_id = %s::uuid AND user_id = %s::uuid AND is_active = TRUE",
        (tenant_id, user_id),
    )
    if not membership:
        raise HTTPException(status_code=404, detail="El usuario no es miembro activo de esta empresa")

    execute(
        db,
        "UPDATE global.user_tenants SET is_active = FALSE WHERE tenant_id = %s::uuid AND user_id = %s::uuid",
        (tenant_id, user_id),
    )
    execute(
        db,
        "UPDATE global.user_tenant_roles SET revoked_at = NOW(), revoked_by = %s::uuid WHERE tenant_id = %s::uuid AND user_id = %s::uuid AND revoked_at IS NULL",
        (actor_user_id, tenant_id, user_id),
    )

    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=tenant_id,
        module="companies",
        action="DELETE",
        entity_type="user_tenants",
        entity_id=user_id,
    )
    return {"detail": "Miembro removido correctamente"}
