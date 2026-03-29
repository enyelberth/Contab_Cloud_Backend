from fastapi import HTTPException

from app.audit import log_audit
from app.database import execute, fetch_all, fetch_one
from app.company import schemas


def create_company(db, company_data: schemas.CompanyCreate, created_by: int):
    existing = fetch_one(db, "SELECT id FROM companies WHERE tax_id = %s AND deleted_at IS NULL", (company_data.tax_id,))
    if existing:
        raise HTTPException(status_code=400, detail="Company tax_id already exists")

    creator = fetch_one(db, "SELECT id FROM users WHERE id = %s", (created_by,))
    if not creator:
        raise HTTPException(status_code=400, detail="Creator user not found")

    company = execute(
        db,
        """
        INSERT INTO companies (
            legal_name, trade_name, tax_id, country,
            accounting_email, phone, address, status, created_by
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', %s)
        RETURNING id, legal_name, trade_name, tax_id, country,
                  accounting_email, phone, address, status, created_by, created_at
        """,
        (
            company_data.legal_name,
            company_data.trade_name,
            company_data.tax_id,
            company_data.country,
            company_data.accounting_email,
            company_data.phone,
            company_data.address,
            created_by,
        ),
        returning=True,
    )

    admin_role = fetch_one(db, "SELECT id FROM roles WHERE name = 'ADMIN_EMPRESA'", ())
    if not admin_role:
        raise HTTPException(status_code=500, detail="ADMIN_EMPRESA role is missing")

    execute(
        db,
        """
        INSERT INTO company_memberships (
            company_id, user_id, role_id,
            is_primary_accountant, access_level, status,
            invited_by, invited_at
        )
        VALUES (%s, %s, %s, TRUE, 'full', 'active', %s, NOW())
        ON CONFLICT (company_id, user_id)
        DO UPDATE SET
            role_id = EXCLUDED.role_id,
            is_primary_accountant = EXCLUDED.is_primary_accountant,
            access_level = EXCLUDED.access_level,
            status = EXCLUDED.status,
            invited_by = EXCLUDED.invited_by,
            invited_at = EXCLUDED.invited_at
        """,
        (
            company["id"],
            created_by,
            admin_role["id"],
            created_by,
        ),
    )

    log_audit(
        db,
        actor_user_id=created_by,
        company_id=company["id"],
        module="companies",
        action="CREATE",
        entity_type="companies",
        entity_id=company["id"],
        after_data=company,
    )

    return company


def get_companies(db, skip: int = 0, limit: int = 100, user_id: int | None = None):
    if user_id is None:
        return fetch_all(
            db,
            """
            SELECT id, legal_name, trade_name, tax_id, country,
                   accounting_email, phone, address, status, created_by, created_at
            FROM companies
            WHERE deleted_at IS NULL
            ORDER BY id ASC
            OFFSET %s LIMIT %s
            """,
            (skip, limit),
        )

    return fetch_all(
        db,
        """
        SELECT c.id, c.legal_name, c.trade_name, c.tax_id, c.country,
               c.accounting_email, c.phone, c.address, c.status, c.created_by, c.created_at
        FROM companies c
        INNER JOIN company_memberships cm ON cm.company_id = c.id
        WHERE cm.user_id = %s
          AND cm.status = 'active'
                    AND cm.deleted_at IS NULL
                    AND c.deleted_at IS NULL
        ORDER BY c.id ASC
        OFFSET %s LIMIT %s
        """,
        (user_id, skip, limit),
    )


def _check_delegation(db, manager_role_id: int, target_role_id: int):
    return fetch_one(
        db,
        """
        SELECT can_assign_role, can_grant_permissions
        FROM role_delegation_rules
        WHERE manager_role_id = %s AND target_role_id = %s
        """,
        (manager_role_id, target_role_id),
    )


def add_company_member(db, company_id: int, data: schemas.CompanyMembershipCreate, invited_by: int):
    company = fetch_one(db, "SELECT id FROM companies WHERE id = %s AND deleted_at IS NULL", (company_id,))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    user = fetch_one(db, "SELECT id FROM users WHERE id = %s AND deleted_at IS NULL", (data.user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = fetch_one(db, "SELECT id, name FROM roles WHERE id = %s AND deleted_at IS NULL", (data.role_id,))
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    inviter_membership = fetch_one(
        db,
        """
        SELECT role_id
        FROM company_memberships
        WHERE company_id = %s
          AND user_id = %s
          AND status = 'active'
                    AND deleted_at IS NULL
        """,
                (company_id, invited_by),
    )
    if not inviter_membership:
        raise HTTPException(status_code=403, detail="Inviter has no active membership in company")

    delegation = _check_delegation(db, inviter_membership["role_id"], data.role_id)
    if not delegation or not delegation["can_assign_role"]:
        raise HTTPException(status_code=403, detail="Inviter cannot assign this role")

    membership = execute(
        db,
        """
        INSERT INTO company_memberships (
            company_id, user_id, role_id,
            is_primary_accountant, access_level,
            status, invited_by, invited_at
        )
        VALUES (%s, %s, %s, FALSE, %s, 'active', %s, NOW())
        ON CONFLICT (company_id, user_id)
        DO UPDATE SET
            role_id = EXCLUDED.role_id,
            access_level = EXCLUDED.access_level,
            status = EXCLUDED.status,
            invited_by = EXCLUDED.invited_by,
            invited_at = EXCLUDED.invited_at
        RETURNING id, company_id, user_id, role_id,
                  is_primary_accountant, access_level,
                  status, invited_by, invited_at, joined_at
        """,
        (
            company_id,
            data.user_id,
            data.role_id,
            data.access_level,
            invited_by,
        ),
        returning=True,
    )
    log_audit(
        db,
        actor_user_id=invited_by,
        company_id=company_id,
        module="company_memberships",
        action="CREATE",
        entity_type="company_memberships",
        entity_id=membership["id"],
        after_data=membership,
    )
    return membership


def get_company_members(db, company_id: int):
    return fetch_all(
        db,
        """
        SELECT id, company_id, user_id, role_id,
               is_primary_accountant, access_level,
               status, invited_by, invited_at, joined_at
        FROM company_memberships
        WHERE company_id = %s
          AND deleted_at IS NULL
        ORDER BY id ASC
        """,
        (company_id,),
    )


def delete_company(db, company_id: int, actor_user_id: int):
    company = fetch_one(
        db,
        """
        SELECT id, legal_name, trade_name, tax_id, country,
               accounting_email, phone, address, status, created_by, created_at
        FROM companies
        WHERE id = %s AND deleted_at IS NULL
        """,
        (company_id,),
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    execute(
        db,
        "UPDATE companies SET deleted_at = NOW(), status = 'archived' WHERE id = %s",
        (company_id,),
    )
    execute(
        db,
        """
        UPDATE company_memberships
        SET deleted_at = NOW(), status = 'removed'
        WHERE company_id = %s AND deleted_at IS NULL
        """,
        (company_id,),
    )
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=company_id,
        module="companies",
        action="DELETE",
        entity_type="companies",
        entity_id=company_id,
        before_data=company,
    )
    return {"detail": "Company archived successfully"}


def remove_company_member(db, company_id: int, user_id: int, actor_user_id: int):
    membership = fetch_one(
        db,
        """
        SELECT id, company_id, user_id, role_id,
               is_primary_accountant, access_level,
               status, invited_by, invited_at, joined_at
        FROM company_memberships
        WHERE company_id = %s
          AND user_id = %s
          AND deleted_at IS NULL
        """,
        (company_id, user_id),
    )
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    execute(
        db,
        """
        UPDATE company_memberships
        SET deleted_at = NOW(), status = 'removed'
        WHERE id = %s
        """,
        (membership["id"],),
    )
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=company_id,
        module="company_memberships",
        action="DELETE",
        entity_type="company_memberships",
        entity_id=membership["id"],
        before_data=membership,
    )
    return {"detail": "Member removed successfully"}
