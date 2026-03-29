from fastapi import HTTPException
from app.audit import log_audit
from app.auth.security import hash_password
from app.user import schemas
from app.database import execute, fetch_all, fetch_one


def _user_exists_by_email_or_username(db, email: str, username: str):
    return fetch_one(
        db,
        """
        SELECT id
        FROM users
                WHERE (email = %s OR username = %s)
                    AND deleted_at IS NULL
        """,
        (email, username),
    )


def get_user(db, user_id: int):
    return fetch_one(
        db,
        """
        SELECT id, username, email, first_name, last_name, user_type,
               branch_id, role_id, status, created_at
        FROM users
        WHERE id = %s
                    AND deleted_at IS NULL
        """,
        (user_id,),
    )


def get_users(db, skip: int = 0, limit: int = 100, company_id: int | None = None):
    if company_id is None:
        return fetch_all(
            db,
            """
            SELECT id, username, email, first_name, last_name, user_type,
                   branch_id, role_id, status, created_at, NULL::INTEGER AS company_id
            FROM users
            WHERE deleted_at IS NULL
            ORDER BY id ASC
            OFFSET %s LIMIT %s
            """,
            (skip, limit),
        )

    return fetch_all(
        db,
        """
        SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.user_type,
               u.branch_id, u.role_id, u.status, u.created_at, cm.company_id
        FROM users u
        INNER JOIN company_memberships cm ON cm.user_id = u.id
        WHERE cm.company_id = %s
          AND cm.status = 'active'
                    AND cm.deleted_at IS NULL
                    AND u.deleted_at IS NULL
        ORDER BY u.id ASC
        OFFSET %s LIMIT %s
        """,
        (company_id, skip, limit),
    )


def create_user(db, user_data: schemas.UserCreate, actor_user_id: int | None = None, company_id: int | None = None):
    if _user_exists_by_email_or_username(db, user_data.email, user_data.username):
        raise HTTPException(status_code=400, detail="Email o username ya existe")

    if user_data.role_id is not None:
        role = fetch_one(db, "SELECT id FROM roles WHERE id = %s", (user_data.role_id,))
        if not role:
            raise HTTPException(status_code=400, detail="Role not found")

    if user_data.branch_id is not None:
        branch = fetch_one(db, "SELECT id FROM branches WHERE id = %s", (user_data.branch_id,))
        if not branch:
            raise HTTPException(status_code=400, detail="Branch not found")

    created = execute(
        db,
        """
        INSERT INTO users (
            username, email, first_name, last_name, user_type,
            password_hash, branch_id, role_id, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, username, email, first_name, last_name, user_type,
                  branch_id, role_id, status, created_at, NULL::INTEGER AS company_id
        """,
        (
            user_data.username,
            user_data.email,
            user_data.first_name,
            user_data.last_name,
            user_data.user_type,
            hash_password(user_data.password),
            user_data.branch_id,
            user_data.role_id,
            user_data.status,
        ),
        returning=True,
    )
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=company_id,
        module="users",
        action="CREATE",
        entity_type="users",
        entity_id=created["id"],
        after_data={k: v for k, v in created.items() if k != "password_hash"},
    )
    return created


def update_user(db, user_id: int, user_data: schemas.UserUpdate, actor_user_id: int | None = None, company_id: int | None = None):
    existing = get_user(db, user_id)
    if not existing:
        return None

    payload = user_data.model_dump(exclude_unset=True)
    if not payload:
        return existing

    password_hash = hash_password(payload["password"]) if payload.get("password") else None

    updated = execute(
        db,
        """
        UPDATE users
        SET
            username = COALESCE(%s, username),
            email = COALESCE(%s, email),
            first_name = COALESCE(%s, first_name),
            last_name = COALESCE(%s, last_name),
            user_type = COALESCE(%s, user_type),
            password_hash = COALESCE(%s, password_hash),
            branch_id = COALESCE(%s, branch_id),
            role_id = COALESCE(%s, role_id),
            status = COALESCE(%s, status)
        WHERE id = %s
        RETURNING id, username, email, first_name, last_name, user_type,
                  branch_id, role_id, status, created_at, NULL::INTEGER AS company_id
        """,
        (
            payload.get("username"),
            payload.get("email"),
            payload.get("first_name"),
            payload.get("last_name"),
            payload.get("user_type"),
            password_hash,
            payload.get("branch_id"),
            payload.get("role_id"),
            payload.get("status"),
            user_id,
        ),
        returning=True,
    )
    log_audit(
        db,
        actor_user_id=actor_user_id,
        company_id=company_id,
        module="users",
        action="UPDATE",
        entity_type="users",
        entity_id=user_id,
        before_data=existing,
        after_data=updated,
    )
    return updated


def delete_user(db, user_id: int, actor_user_id: int | None = None, company_id: int | None = None):
    existing = get_user(db, user_id)
    if not existing:
        return False

    row = execute(
        db,
        """
        UPDATE users
        SET deleted_at = NOW(),
            status = 'inactive'
        WHERE id = %s
          AND deleted_at IS NULL
        RETURNING id
        """,
        (user_id,),
        returning=True,
    )
    if row is not None:
        execute(
            db,
            """
            UPDATE company_memberships
            SET deleted_at = NOW(),
                status = 'removed'
            WHERE user_id = %s
              AND deleted_at IS NULL
            """,
            (user_id,),
        )
        log_audit(
            db,
            actor_user_id=actor_user_id,
            company_id=company_id,
            module="users",
            action="DELETE",
            entity_type="users",
            entity_id=user_id,
            before_data=existing,
        )
    return row is not None