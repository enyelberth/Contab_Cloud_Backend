from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.role import schemas
from app import models



class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def create_permission(self, permission_data):
        new_permission = models.Permission(
            name=permission_data.name,
            slug=permission_data.slug
        )
        self.db.add(new_permission)
        self.db.commit()
        self.db.refresh(new_permission)
        return new_permission
    def get_permission(self, permission_id):
        permission = self.db.query(models.Permission).filter(models.Permission.id == permission_id).first()
        if not permission:
            raise HTTPException(status_code=404, detail="Permission not found")
        return permission   
    def delete_permission(self, permission_id):
        permission = self.get_permission(permission_id)
        self.db.delete(permission)
        self.db.commit()
        return permission   
    def get_permissions(self):
        try:
            permissions = self.db.query(models.Permission).all()
            print(f"Permissions retrieved: {permissions}")
            return permissions
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) 
        
    def assign_permissions_to_role(self, role_id, permission_ids):
        role = self.db.query(models.Role).filter(models.Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        permissions = self.db.query(models.Permission).filter(models.Permission.id.in_(permission_ids)).all()
        if len(permissions) != len(permission_ids):
            raise HTTPException(status_code=400, detail="One or more permissions not found")
        
        role.permissions = permissions
        self.db.commit()
        self.db.refresh(role)
        return role
    