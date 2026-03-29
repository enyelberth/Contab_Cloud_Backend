from fastapi import HTTPException
from app.user import schemas
from app.database import execute, fetch_all, fetch_one


def _user_exists_by_email_or_username(db, email: str, username: str):
    return fetch_one(
        db,
        """
        SELECT id
        FROM users
        WHERE email = %s OR username = %s
        """,
        (email, username),
    )


def get_user(db, user_id: int):
    return fetch_one(
        db,
        """
        SELECT id, username, email, branch_id, role_id, status, created_at
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )


def get_users(db, skip: int = 0, limit: int = 100):
    return fetch_all(
        db,
        """
        SELECT id, username, email, branch_id, role_id, status, created_at
        FROM users
        ORDER BY id ASC
        OFFSET %s LIMIT %s
        """,
        (skip, limit),
    )


def create_user(db, user_data: schemas.UserCreate):
    if _user_exists_by_email_or_username(db, user_data.email, user_data.username):
        raise HTTPException(status_code=400, detail="Email o username ya existe")

    return execute(
        db,
        """
        INSERT INTO users (username, email, password_hash, branch_id, role_id, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, username, email, branch_id, role_id, status, created_at
        """,
        (
            user_data.username,
            user_data.email,
            user_data.password,
            user_data.branch_id,
            user_data.role_id,
            user_data.status,
        ),
        returning=True,
    )


def update_user(db, user_id: int, user_data: schemas.UserUpdate):
    existing = get_user(db, user_id)
    if not existing:
        return None

    payload = user_data.model_dump(exclude_unset=True)
    if not payload:
        return existing

    return execute(
        db,
        """
        UPDATE users
        SET
            username = COALESCE(%s, username),
            email = COALESCE(%s, email),
            password_hash = COALESCE(%s, password_hash),
            branch_id = COALESCE(%s, branch_id),
            role_id = COALESCE(%s, role_id),
            status = COALESCE(%s, status)
        WHERE id = %s
        RETURNING id, username, email, branch_id, role_id, status, created_at
        """,
        (
            payload.get("username"),
            payload.get("email"),
            payload.get("password"),
            payload.get("branch_id"),
            payload.get("role_id"),
            payload.get("status"),
            user_id,
        ),
        returning=True,
    )


def delete_user(db, user_id: int):
    row = execute(
        db,
        """
        DELETE FROM users
        WHERE id = %s
        RETURNING id
        """,
        (user_id,),
        returning=True,
    )
    return row is not None