from fastapi import APIRouter, Depends

from app.auth import schemas, service
from app.auth.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db=Depends(get_db)):
    return service.authenticate_user(db, payload)


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh(payload: schemas.RefreshTokenRequest, db=Depends(get_db)):
    return service.refresh_access_token(db, payload)


@router.post("/logout")
def logout(payload: schemas.LogoutRequest, db=Depends(get_db), current_user=Depends(get_current_user)):
    return service.logout(db, current_user_id=current_user["id"], payload=payload)


@router.get("/me", response_model=schemas.CurrentUserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user
