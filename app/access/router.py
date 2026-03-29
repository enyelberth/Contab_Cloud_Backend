from fastapi import APIRouter, Depends

from app.auth.dependencies import require_permission
from app.access import schemas, service
from app.database import get_db

router = APIRouter(prefix="/access", tags=["access"])


@router.get(
    "/companies/{company_id}/users/{user_id}/menus",
    response_model=schemas.UserMenusResponse,
)
def read_user_menus(
    company_id: int,
    user_id: int,
    db=Depends(get_db),
    _=Depends(require_permission("users.view")),
):
    return service.get_user_menus(db, user_id=user_id, company_id=company_id)


@router.get(
    "/companies/{company_id}/users/{user_id}/permissions",
    response_model=schemas.UserPermissionsResponse,
)
def read_user_permissions(
    company_id: int,
    user_id: int,
    db=Depends(get_db),
    _=Depends(require_permission("users.view")),
):
    return service.get_user_permissions(db, user_id=user_id, company_id=company_id)


@router.get(
    "/companies/{company_id}/delegation/check",
    response_model=schemas.DelegationCheckResponse,
)
def check_role_delegation(
    company_id: int,
    manager_user_id: int,
    target_role_id: int,
    db=Depends(get_db),
    _=Depends(require_permission("users.assign_permissions")),
):
    return service.check_delegation(
        db,
        manager_user_id=manager_user_id,
        company_id=company_id,
        target_role_id=target_role_id,
    )
