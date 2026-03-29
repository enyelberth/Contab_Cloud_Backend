from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.branche import schemas, service

router = APIRouter(prefix="/branches", tags=["branches"])

@router.post("/", response_model=schemas.Branch)
def create_branch(branch_in: schemas.BranchCreate, db: Session = Depends(get_db)):
    try:
        return service.create_branch(db=db, branch_data=branch_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[schemas.Branch])
def list_branches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_branches(db=db, skip=skip, limit=limit)


@router.get("/{branch_id}", response_model=schemas.Branch)
def read_branch(branch_id: int, db: Session = Depends(get_db)):
    return service.get_branch(db=db, branch_id=branch_id)


@router.put("/{branch_id}", response_model=schemas.Branch)
def update_branch(branch_id: int, branch_in: schemas.BranchUpdate, db: Session = Depends(get_db)):
    return service.update_branch(db=db, branch_id=branch_id, branch_data=branch_in)


@router.delete("/{branch_id}", response_model=schemas.Branch)
def delete_branch(branch_id: int, db: Session = Depends(get_db)):
    return service.delete_branch(db=db, branch_id=branch_id)