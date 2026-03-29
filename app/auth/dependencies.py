from fastapi import Depends, Header, HTTPException, Request, status

from app.auth import security, service
from app.database import fetch_one, get_db


def get_current_user(db=Depends(get_db), authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = security.decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    sub = payload.get("sub")
    if not sub or not str(sub).isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return service.get_current_user_profile(db, int(sub))


def _has_permission_in_role(db, role_id: int | None, permission_slug: str) -> bool:
    if role_id is None:
        return False
    row = fetch_one(
        db,
        """
        SELECT 1 AS ok
        FROM role_permissions rp
                INNER JOIN roles r ON r.id = rp.role_id
        INNER JOIN permissions p ON p.id = rp.permission_id
        WHERE rp.role_id = %s
          AND p.slug = %s
                    AND r.deleted_at IS NULL
                    AND p.deleted_at IS NULL
        LIMIT 1
        """,
        (role_id, permission_slug),
    )
    return row is not None


def require_permission(permission_slug: str, company_scoped: bool = True):
    def dependency(
        request: Request,
        db=Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        if not company_scoped:
            if _has_permission_in_role(db, current_user.get("role_id"), permission_slug):
                return current_user
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

        company_id = request.path_params.get("company_id") or request.query_params.get("company_id")
        if company_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="company_id is required")
        if not str(company_id).isdigit():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="company_id must be numeric")

        membership = fetch_one(
            db,
            """
            SELECT role_id
            FROM company_memberships
            WHERE company_id = %s
              AND user_id = %s
              AND status = 'active'
                            AND deleted_at IS NULL
            """,
            (int(company_id), current_user["id"]),
        )
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active membership")

        if _has_permission_in_role(db, membership["role_id"], permission_slug):
            return current_user

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    return dependency
