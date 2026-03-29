from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.dependencies import require_permission
from app.database import get_db
from app.user import schemas, service

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: schemas.UserCreate, company_id: int, db=Depends(get_db), current_user=Depends(require_permission("users.create"))):
    return service.create_user(db=db, user_data=user_in, actor_user_id=current_user["id"], company_id=company_id)

@router.get("/", response_model=List[schemas.UserResponse])
def list_users(skip: int = 0, limit: int = 100, company_id: int | None = None, db=Depends(get_db), _=Depends(require_permission("users.view"))):
    return service.get_users(db=db, skip=skip, limit=limit, company_id=company_id)

@router.get("/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: int, company_id: int, db=Depends(get_db), _=Depends(require_permission("users.view"))):
    db_user = service.get_user(db=db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user_in: schemas.UserUpdate, company_id: int, db=Depends(get_db), current_user=Depends(require_permission("users.update"))):
    db_user = service.update_user(db=db, user_id=user_id, user_data=user_in, actor_user_id=current_user["id"], company_id=company_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int, company_id: int, db=Depends(get_db), current_user=Depends(require_permission("users.delete"))):
    success = service.delete_user(db=db, user_id=user_id, actor_user_id=current_user["id"], company_id=company_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}