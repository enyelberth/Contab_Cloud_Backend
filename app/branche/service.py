from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.branche import schemas
from app import models
from datetime import datetime


def get_branch(db: Session, branch_id: int):
    branch = db.query(models.Branch).filter(
        models.Branch.id == branch_id,
        models.Branch.deleted_at == None
    ).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch


def get_branches(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Branch).filter(
        models.Branch.deleted_at == None
    ).offset(skip).limit(limit).all()


def create_branch(db: Session, branch_data: schemas.BranchCreate):
    new_branch = models.Branch(
        name=branch_data.name,
        address=branch_data.address,
        phone=branch_data.phone,
        is_active=branch_data.is_active
    )
    db.add(new_branch)
    db.commit()
    db.refresh(new_branch)
    return new_branch


def update_branch(db: Session, branch_id: int, branch_data: schemas.BranchUpdate):
    branch = get_branch(db, branch_id)

    if branch_data.name is not None:
        branch.name = branch_data.name
    if branch_data.address is not None:
        branch.address = branch_data.address
    if branch_data.phone is not None:
        branch.phone = branch_data.phone
    if branch_data.is_active is not None:
        branch.is_active = branch_data.is_active

    db.commit()
    db.refresh(branch)
    return branch


def delete_branch(db: Session, branch_id: int):
    branch = get_branch(db, branch_id)
    branch.deleted_at = datetime.utcnow()
    db.commit()
    return branch