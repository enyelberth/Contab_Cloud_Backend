from fastapi import HTTPException, status

from app.audit import log_audit
from app.auth import schemas, security
from app.database import execute, fetch_one


def _get_user_by_email(db, email: str):
    return fetch_one(
        db,
        """
     SELECT u.uuid::text AS id,
         u.username,
         u.email,
         p.first_name,
         p.first_lastname AS last_name,
         u.status,
         u.password_hash
     FROM global.users u
     LEFT JOIN global.profiles p ON p.user_id = u.uuid
     WHERE u.email = %s
       AND u.deleted_at IS NULL
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
        INSERT INTO security.user_sessions (user_id, token_hash, expires_at)
        VALUES (%s::uuid, %s, %s)
        """,
        (user["id"], refresh_hash, refresh_expires),
    )

    execute(
        db,
        "UPDATE global.users SET last_login_at = NOW() WHERE uuid = %s::uuid",
        (user["id"],),
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
                SELECT uuid::text AS id, user_id::text AS user_id
                FROM security.user_sessions
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
    new_refresh_raw, new_refresh_hash, new_refresh_exp, _new_jti = security.create_refresh_token()

    execute(
        db,
        """
        UPDATE security.user_sessions
        SET revoked_at = NOW(), revoked_reason = 'rotated'
        WHERE uuid = %s::uuid
        """,
        (row["id"],),
    )
    execute(
        db,
        """
        INSERT INTO security.user_sessions (user_id, token_hash, expires_at)
        VALUES (%s::uuid, %s, %s)
        """,
        (user["id"], new_refresh_hash, new_refresh_exp),
    )

    log_audit(
        db,
        actor_user_id=user["id"],
        company_id=None,
        module="auth",
        action="REFRESH",
        entity_type="users",
        entity_id=user["id"],
        before_data={"session_id": row["id"]},
    )

    return schemas.TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_raw,
        expires_at=expires_at,
    )


def logout(db, current_user_id: str, payload: schemas.LogoutRequest):
    refresh_hash = security.hash_refresh_token(payload.refresh_token)
    row = fetch_one(
        db,
        """
                SELECT uuid::text AS id
                FROM security.user_sessions
                WHERE user_id = %s::uuid
          AND token_hash = %s
          AND revoked_at IS NULL
        """,
        (current_user_id, refresh_hash),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token already revoked or invalid")

    execute(
        db,
        "UPDATE security.user_sessions SET revoked_at = NOW(), revoked_reason = 'logout' WHERE uuid = %s::uuid",
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


def get_current_user_profile(db, user_id: str):
    user = fetch_one(
        db,
        """
     SELECT u.uuid::text AS id,
         u.username,
         u.email,
         p.first_name,
         p.first_lastname AS last_name,
         ut.tenant_id::text AS tenant_id,
         utr.role_id::text AS role_id,
         r.name AS role_name,
         gr.name AS global_role_name,
         u.status
     FROM global.users u
     LEFT JOIN global.profiles p ON p.user_id = u.uuid
     LEFT JOIN global.user_tenants ut ON ut.user_id = u.uuid AND ut.is_active = TRUE
     LEFT JOIN global.user_tenant_roles utr
         ON utr.user_id = u.uuid
        AND (ut.tenant_id IS NULL OR utr.tenant_id = ut.tenant_id)
        AND utr.revoked_at IS NULL
     LEFT JOIN global.roles r ON r.uuid = utr.role_id
     LEFT JOIN global.user_global_roles ugr
         ON ugr.user_id = u.uuid AND ugr.revoked_at IS NULL
     LEFT JOIN global.roles gr ON gr.uuid = ugr.role_id
     WHERE u.uuid = %s::uuid
       AND u.deleted_at IS NULL
     ORDER BY ut.created_at DESC NULLS LAST, utr.assigned_at DESC NULLS LAST
     LIMIT 1
        """,
        (user_id,),
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
