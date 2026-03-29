from fastapi import HTTPException

from app.database import fetch_all, fetch_one


def _membership(db, user_id: int, company_id: int):
    membership = fetch_one(
        db,
        """
        SELECT cm.role_id, r.name AS role_name
        FROM company_memberships cm
        INNER JOIN roles r ON r.id = cm.role_id
        WHERE cm.user_id = %s
          AND cm.company_id = %s
          AND cm.status = 'active'
                    AND cm.deleted_at IS NULL
                    AND r.deleted_at IS NULL
        """,
        (user_id, company_id),
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Active membership not found")
    return membership


def get_user_menus(db, user_id: int, company_id: int):
    membership = _membership(db, user_id, company_id)

    menus = fetch_all(
        db,
        """
        SELECT fm.id AS menu_id,
               fm.menu_key,
               fm.label,
               fm.path,
               fm.icon,
               am.module_key,
               am.name AS module_name,
               rma.can_view,
               rma.can_create,
               rma.can_update,
               rma.can_delete,
               rma.can_assign_permissions
        FROM role_menu_access rma
        INNER JOIN frontend_menus fm ON fm.id = rma.menu_id AND fm.is_active = TRUE
        INNER JOIN app_modules am ON am.id = fm.module_id AND am.is_active = TRUE
        WHERE rma.role_id = %s
          AND rma.can_view = TRUE
        ORDER BY am.sort_order, fm.sort_order
        """,
        (membership["role_id"],),
    )

    return {
        "user_id": user_id,
        "company_id": company_id,
        "role_id": membership["role_id"],
        "role_name": membership["role_name"],
        "menus": menus,
    }


def get_user_permissions(db, user_id: int, company_id: int):
    membership = _membership(db, user_id, company_id)

    permissions = fetch_all(
        db,
        """
        SELECT p.id, p.name, p.slug
        FROM role_permissions rp
        INNER JOIN permissions p ON p.id = rp.permission_id
        WHERE rp.role_id = %s
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


def check_delegation(db, manager_user_id: int, company_id: int, target_role_id: int):
    membership = _membership(db, manager_user_id, company_id)

    rule = fetch_one(
        db,
        """
        SELECT can_assign_role, can_grant_permissions
        FROM role_delegation_rules
        WHERE manager_role_id = %s
          AND target_role_id = %s
        """,
        (membership["role_id"], target_role_id),
    )

    if not rule:
        return {
            "manager_user_id": manager_user_id,
            "company_id": company_id,
            "manager_role_id": membership["role_id"],
            "target_role_id": target_role_id,
            "can_assign_role": False,
            "can_grant_permissions": False,
        }

    return {
        "manager_user_id": manager_user_id,
        "company_id": company_id,
        "manager_role_id": membership["role_id"],
        "target_role_id": target_role_id,
        "can_assign_role": rule["can_assign_role"],
        "can_grant_permissions": rule["can_grant_permissions"],
    }
