from fastapi import HTTPException
from app.database import execute, fetch_all, fetch_one



class PermissionService:
    def __init__(self, db):
        self.db = db

    def create_permission(self, permission_data):
        existing = fetch_one(
            self.db,
            "SELECT id FROM permissions WHERE slug = %s",
            (permission_data.slug,),
        )
        if existing:
            raise HTTPException(status_code=400, detail="Permission slug already exists")
        return execute(
            self.db,
            """
            INSERT INTO permissions (name, slug)
            VALUES (%s, %s)
            RETURNING id, name, slug
            """,
            (permission_data.name, permission_data.slug),
            returning=True,
        )

    def get_permission(self, permission_id):
        permission = fetch_one(
            self.db,
            "SELECT id, name, slug FROM permissions WHERE id = %s",
            (permission_id,),
        )
        if not permission:
            raise HTTPException(status_code=404, detail="Permission not found")
        return permission   

    def delete_permission(self, permission_id):
        permission = self.get_permission(permission_id)
        execute(
            self.db,
            "DELETE FROM permissions WHERE id = %s",
            (permission_id,),
            returning=False,
        )
        return permission   

    def get_permissions(self):
        return fetch_all(
            self.db,
            "SELECT id, name, slug FROM permissions ORDER BY id ASC",
        )

    def get_permission_roles(self, permission_id):
        self.get_permission(permission_id)
        roles = fetch_all(
            self.db,
            """
            SELECT r.id, r.name, r.description
            FROM roles r
            INNER JOIN role_permissions rp ON rp.role_id = r.id
            WHERE rp.permission_id = %s
            ORDER BY r.id ASC
            """,
            (permission_id,),
        )
        for role in roles:
            role["permissions"] = fetch_all(
                self.db,
                """
                SELECT p.id, p.name, p.slug
                FROM permissions p
                INNER JOIN role_permissions rp ON rp.permission_id = p.id
                WHERE rp.role_id = %s
                ORDER BY p.id ASC
                """,
                (role["id"],),
            )
        return roles
        
    def assign_permissions_to_role(self, role_id, permission_ids):
        role = fetch_one(
            self.db,
            "SELECT id, name, description FROM roles WHERE id = %s",
            (role_id,),
        )
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        permissions = fetch_all(
            self.db,
            "SELECT id FROM permissions WHERE id = ANY(%s)",
            (permission_ids,),
        )
        if len(permissions) != len(set(permission_ids)):
            raise HTTPException(status_code=400, detail="One or more permissions not found")
        
        execute(
            self.db,
            "DELETE FROM role_permissions WHERE role_id = %s",
            (role_id,),
            returning=False,
        )
        with self.db.cursor() as cur:
            cur.executemany(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                [(role_id, permission_id) for permission_id in permission_ids],
            )
        self.db.commit()

        role["permissions"] = fetch_all(
            self.db,
            """
            SELECT p.id, p.name, p.slug
            FROM permissions p
            INNER JOIN role_permissions rp ON rp.permission_id = p.id
            WHERE rp.role_id = %s
            ORDER BY p.id ASC
            """,
            (role_id,),
        )
        return role
    