from fastapi import HTTPException
from app.database import execute, fetch_all, fetch_one


def _get_role_permissions(db, role_id: int):
    return fetch_all(
        db,
        """
        SELECT p.id, p.name, p.slug
        FROM permissions p
        INNER JOIN role_permissions rp ON rp.permission_id = p.id
        WHERE rp.role_id = %s
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
        SELECT id, name, description
        FROM roles
        WHERE id = %s
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
        SELECT id, name, description
        FROM roles
        ORDER BY id ASC
        OFFSET %s LIMIT %s
        """,
        (skip, limit),
    )
    return [_role_with_permissions(db, role) for role in roles]


def create_role(db, role_data):
    existing_role = fetch_one(
        db,
        "SELECT id FROM roles WHERE name = %s",
        (role_data.name,),
    )
    if existing_role:
        raise HTTPException(status_code=400, detail="Role name already exists")

    new_role = execute(
        db,
        """
        INSERT INTO roles (name, description)
        VALUES (%s, %s)
        RETURNING id, name, description
        """,
        (role_data.name, role_data.description),
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

    return _role_with_permissions(db, new_role)


def update_role(db, role_id: int, role_data):
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
            description = COALESCE(%s, description)
        WHERE id = %s
        RETURNING id, name, description
        """,
        (role_data.name, role_data.description, role_id),
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

    return _role_with_permissions(db, updated or role)


def delete_role(db, role_id: int):
    role = get_role(db, role_id)
    execute(
        db,
        "DELETE FROM roles WHERE id = %s",
        (role_id,),
        returning=False,
    )
    return role

