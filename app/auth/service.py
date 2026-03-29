from fastapi import HTTPException, status

from app.audit import log_audit
from app.auth import schemas, security
from app.database import execute, fetch_one


def _get_user_by_email(db, email: str):
    return fetch_one(
        db,
        """
        SELECT id, username, email, first_name, last_name, user_type,
               role_id, status, password_hash
        FROM users
        WHERE email = %s
          AND deleted_at IS NULL
        """,
        (email,),
    )


def authenticate_user(db, data: schemas.LoginRequest):
    user = _get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user["status"] != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    if not security.verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, expires_at = security.create_access_token(user["id"])
    refresh_raw, refresh_hash, refresh_expires, jti = security.create_refresh_token()

    execute(
        db,
        """
        INSERT INTO auth_refresh_tokens (user_id, token_hash, jti, expires_at)
        VALUES (%s, %s, %s, %s)
        """,
        (user["id"], refresh_hash, jti, refresh_expires),
    )

    log_audit(
        db,
        actor_user_id=user["id"],
        company_id=None,
        module="auth",
        action="LOGIN",
        entity_type="users",
        entity_id=user["id"],
        after_data={"jti": jti},
    )

    return schemas.TokenResponse(access_token=token, refresh_token=refresh_raw, expires_at=expires_at)


def refresh_access_token(db, payload: schemas.RefreshTokenRequest):
    refresh_hash = security.hash_refresh_token(payload.refresh_token)
    row = fetch_one(
        db,
        """
        SELECT id, user_id, jti
        FROM auth_refresh_tokens
        WHERE token_hash = %s
          AND revoked_at IS NULL
          AND expires_at > NOW()
        """,
        (refresh_hash,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = get_current_user_profile(db, row["user_id"])
    if user["status"] != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    access_token, expires_at = security.create_access_token(user["id"])
    new_refresh_raw, new_refresh_hash, new_refresh_exp, new_jti = security.create_refresh_token()

    execute(
        db,
        """
        UPDATE auth_refresh_tokens
        SET revoked_at = NOW(), replaced_by_jti = %s
        WHERE id = %s
        """,
        (new_jti, row["id"]),
    )
    execute(
        db,
        """
        INSERT INTO auth_refresh_tokens (user_id, token_hash, jti, expires_at)
        VALUES (%s, %s, %s, %s)
        """,
        (user["id"], new_refresh_hash, new_jti, new_refresh_exp),
    )

    log_audit(
        db,
        actor_user_id=user["id"],
        company_id=None,
        module="auth",
        action="REFRESH",
        entity_type="users",
        entity_id=user["id"],
        before_data={"jti": row["jti"]},
        after_data={"jti": new_jti},
    )

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_raw,
        expires_at=expires_at,
    )


def logout(db, current_user_id: int, payload: schemas.LogoutRequest):
    refresh_hash = security.hash_refresh_token(payload.refresh_token)
    row = fetch_one(
        db,
        """
        SELECT id
        FROM auth_refresh_tokens
        WHERE user_id = %s
          AND token_hash = %s
          AND revoked_at IS NULL
        """,
        (current_user_id, refresh_hash),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token already revoked or invalid")

    execute(
        db,
        "UPDATE auth_refresh_tokens SET revoked_at = NOW() WHERE id = %s",
        (row["id"],),
    )

    log_audit(
        db,
        actor_user_id=current_user_id,
        company_id=None,
        module="auth",
        action="LOGOUT",
        entity_type="users",
        entity_id=current_user_id,
    )

    return {"detail": "Logout successful"}


def get_current_user_profile(db, user_id: int):
    user = fetch_one(
        db,
        """
        SELECT id, username, email, first_name, last_name, user_type,
               role_id, status
        FROM users
        WHERE id = %s
          AND deleted_at IS NULL
        """,
        (user_id,),
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
