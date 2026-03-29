from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.user import schemas
from app import models

# Importa tu lógica de hashing aquí (ejemplo con passlib o similar)

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user_data: schemas.UserCreate):
    # Recuerda hashear la contraseña aquí antes de guardar
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        password_hash=user_data.password, # ¡HASHEAR ESTO!
        branch_id=user_data.branch_id,
        role_id=user_data.role_id,
        status=user_data.status
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_data: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if db_user:
        user_dict = user_data.model_dump(exclude_unset=True)
        for key, value in user_dict.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False