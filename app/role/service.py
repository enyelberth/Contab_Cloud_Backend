from fastapi import HTTPException
from app.audit import log_audit
from app.database import execute, fetch_all, fetch_one


def _get_role_permissions(db, role_id: int):
    return fetch_all(
        db,
        """
        SELECT p.id, p.name, p.slug
        FROM permissions p
        INNER JOIN role_permissions rp ON rp.permission_id = p.id
        WHERE rp.role_id = %s
                    AND p.deleted_at IS NULL
        ORDER BY p.id ASC
        """,
        (role_id,),
    )


def _role_with_permissions(db, role_row):
    if not role_row:
        return None
    role_data = dict(role_row)
    role_data["permissions"] = _get_role_permissions(db, role_data["id"])
    return role_data


def get_role(db, role_id: int):
    role = fetch_one(
        db,
        """
        SELECT id, name, description, scope, is_assignable_to_client
        FROM roles
        WHERE id = %s
                    AND deleted_at IS NULL
        """,
        (role_id,),
    )
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return _role_with_permissions(db, role)


def get_roles(db, skip: int = 0, limit: int = 100):
    roles = fetch_all(
        db,
        """
        SELECT id, name, description, scope, is_assignable_to_client
        FROM roles
        WHERE deleted_at IS NULL
        ORDER BY id ASC
        OFFSET %s LIMIT %s
        """,
        (skip, limit),
    )
    return [_role_with_permissions(db, role) for role in roles]


def create_role(db, role_data, actor_user_id: int | None = None, company_id: int | None = None):
    existing_role = fetch_one(
        db,
        "SELECT id FROM roles WHERE name = %s AND deleted_at IS NULL",
        (role_data.name,),
    )
    if existing_role:
        raise HTTPException(status_code=400, detail="Role name already exists")

    new_role = execute(
        db,
        """
        INSERT INTO roles (name, description, scope, is_assignable_to_client)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, description, scope, is_assignable_to_client
        """,
        (
            role_data.name,
            role_data.description,
            role_data.scope,
            role_data.is_assignable_to_client,
        ),
        returning=True,
    )

    if role_data.permissions_ids:
        permissions = fetch_all(
            db,
            "SELECT id FROM permissions WHERE id = ANY(%s)",
            (role_data.permissions_ids,),
        )
        if len(permissions) != len(set(role_data.permissions_ids)):
            raise HTTPException(status_code=400, detail="One or more permissions not found")
        with db.cursor() as cur:
            cur.executemany(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                [(new_role["id"], permission_id) for permission_id in role_data.permissions_ids],
            )
        db.commit()

    enriched = _role_with_permissions(db, new_role)
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=company_id,
        module="roles",
        action="CREATE",
        entity_type="roles",
        entity_id=new_role["id"],
        after_data=enriched,
    )
    return enriched


def update_role(db, role_id: int, role_data, actor_user_id: int | None = None, company_id: int | None = None):
    role = get_role(db, role_id)

    if role_data.name is not None:
        existing_role = fetch_one(
            db,
            "SELECT id FROM roles WHERE name = %s AND id <> %s",
            (role_data.name, role_id),
        )
        if existing_role:
            raise HTTPException(status_code=400, detail="Role name already exists")
    updated = execute(
        db,
        """
        UPDATE roles
        SET
            name = COALESCE(%s, name),
            description = COALESCE(%s, description),
            scope = COALESCE(%s, scope),
            is_assignable_to_client = COALESCE(%s, is_assignable_to_client)
        WHERE id = %s
        RETURNING id, name, description, scope, is_assignable_to_client
        """,
        (
            role_data.name,
            role_data.description,
            role_data.scope,
            role_data.is_assignable_to_client,
            role_id,
        ),
        returning=True,
    )

    if role_data.permissions_ids is not None:
        execute(
            db,
            "DELETE FROM role_permissions WHERE role_id = %s",
            (role_id,),
            returning=False,
        )
        if role_data.permissions_ids:
            permissions = fetch_all(
                db,
                "SELECT id FROM permissions WHERE id = ANY(%s)",
                (role_data.permissions_ids,),
            )
            if len(permissions) != len(set(role_data.permissions_ids)):
                raise HTTPException(status_code=400, detail="One or more permissions not found")
            with db.cursor() as cur:
                cur.executemany(
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    [(role_id, permission_id) for permission_id in role_data.permissions_ids],
                )
            db.commit()

    enriched = _role_with_permissions(db, updated or role)
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=company_id,
        module="roles",
        action="UPDATE",
        entity_type="roles",
        entity_id=role_id,
        before_data=role,
        after_data=enriched,
    )
    return enriched


def delete_role(db, role_id: int, actor_user_id: int | None = None, company_id: int | None = None):
    role = get_role(db, role_id)
    execute(
        db,
        "UPDATE roles SET deleted_at = NOW() WHERE id = %s AND deleted_at IS NULL",
        (role_id,),
        returning=False,
    )
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=company_id,
        module="roles",
        action="DELETE",
        entity_type="roles",
        entity_id=role_id,
        before_data=role,
    )
    return role

