from typing import List

from fastapi import APIRouter, Depends
from app.database import get_db
from app.role import schemas, service

router = APIRouter(prefix="/roles", tags=["roles"])

@router.post("/", response_model=schemas.Role)
def create_role(role_in: schemas.RoleCreate, db=Depends(get_db)):
    return service.create_role(db=db, role_data=role_in)


@router.get("/", response_model=List[schemas.Role])
def list_roles(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    return service.get_roles(db=db, skip=skip, limit=limit)


@router.get("/{role_id}", response_model=schemas.Role)
def read_role(role_id: int, db=Depends(get_db)):
    return service.get_role(db=db, role_id=role_id)


@router.put("/{role_id}", response_model=schemas.Role)
def update_role(role_id: int, role_in: schemas.RoleUpdate, db=Depends(get_db)):
    return service.update_role(db=db, role_id=role_id, role_data=role_in)


@router.delete("/{role_id}", response_model=schemas.Role)
def delete_role(role_id: int, db=Depends(get_db)):
    return service.delete_role(db=db, role_id=role_id)
