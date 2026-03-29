from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.role import schemas
from app import models


def get_role(db: Session, role_id: int):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


def get_roles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Role).offset(skip).limit(limit).all()


def create_role(db: Session, role_data: schemas.RoleCreate):
    # Check if role name already exists
    existing_role = db.query(models.Role).filter(models.Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="Role name already exists")
    
    new_role = models.Role(
        name=role_data.name,
        description=role_data.description
    )

    if role_data.permissions_ids:
        permissions = db.query(models.Permission).filter(models.Permission.id.in_(role_data.permissions_ids)).all()
        if len(permissions) != len(role_data.permissions_ids):
            raise HTTPException(status_code=400, detail="One or more permissions not found")
        new_role.permissions = permissions

    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


def update_role(db: Session, role_id: int, role_data: schemas.RoleUpdate):
    role = get_role(db, role_id)

    if role_data.name is not None:
        # Check if new name conflicts
        existing_role = db.query(models.Role).filter(
            models.Role.name == role_data.name,
            models.Role.id != role_id
        ).first()
        if existing_role:
            raise HTTPException(status_code=400, detail="Role name already exists")
        role.name = role_data.name

    if role_data.description is not None:
        role.description = role_data.description

    if role_data.permissions_ids is not None:
        if role_data.permissions_ids == []:
            role.permissions = []
        else:
            permissions = db.query(models.Permission).filter(models.Permission.id.in_(role_data.permissions_ids)).all()
            if len(permissions) != len(role_data.permissions_ids):
                raise HTTPException(status_code=400, detail="One or more permissions not found")
            role.permissions = permissions

    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: int):
    role = get_role(db, role_id)
    db.delete(role)
    db.commit()
    return role

