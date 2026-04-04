from fastapi import HTTPException

from app.database import fetch_all, fetch_one


def _membership(db, user_id: str, company_id: str):
    membership = fetch_one(
        db,
        """
                SELECT utr.role_id::text AS role_id, r.name AS role_name
                FROM global.user_tenants ut
                INNER JOIN global.user_tenant_roles utr
                                ON utr.user_id = ut.user_id
                             AND utr.tenant_id = ut.tenant_id
                             AND utr.revoked_at IS NULL
                INNER JOIN global.roles r ON r.uuid = utr.role_id
                WHERE ut.user_id = %s::uuid
                    AND ut.tenant_id = %s::uuid
                    AND ut.is_active = TRUE
                    AND r.deleted_at IS NULL
                ORDER BY utr.assigned_at DESC
                LIMIT 1
        """,
        (user_id, company_id),
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Active membership not found")
    return membership


def get_user_menus(db, user_id: str, company_id: str):
    membership = _membership(db, user_id, company_id)

    return {
        "user_id": user_id,
        "company_id": company_id,
        "role_id": membership["role_id"],
        "role_name": membership["role_name"],
        "menus": [],
    }


def get_user_permissions(db, user_id: str, company_id: str):
    membership = _membership(db, user_id, company_id)

    permissions = fetch_all(
        db,
        """
        SELECT p.uuid::text AS id, p.name, p.slug
        FROM global.role_permissions rp
        INNER JOIN global.permissions p ON p.uuid = rp.permission_id
        WHERE rp.role_id = %s::uuid
          AND p.deleted_at IS NULL
        ORDER BY p.slug ASC
        """,
        (membership["role_id"],),
    )

    return {
        "user_id": user_id,
        "company_id": company_id,
        "role_id": membership["role_id"],
        "role_name": membership["role_name"],
        "permissions": permissions,
    }


def check_delegation(db, manager_user_id: str, company_id: str, target_role_id: str):
    membership = _membership(db, manager_user_id, company_id)

    can_grant = fetch_one(
        db,
        """
        SELECT 1 AS ok
        FROM global.role_permissions rp
        JOIN global.permissions p ON p.uuid = rp.permission_id
        WHERE rp.role_id = %s::uuid
          AND p.slug = 'users.assign_permissions'
          AND p.deleted_at IS NULL
        LIMIT 1
        """,
        (membership["role_id"],),
    ) is not None

    return {
        "manager_user_id": manager_user_id,
        "company_id": company_id,
        "manager_role_id": membership["role_id"],
        "target_role_id": target_role_id,
        "can_assign_role": can_grant,
        "can_grant_permissions": can_grant,
    }
