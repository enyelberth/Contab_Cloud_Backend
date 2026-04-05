from __future__ import annotations

from typing import Any

from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from app.auth.security import hash_password


PERMISSIONS: tuple[dict[str, str], ...] = (
    # Empresas / Tenants
    {"module": "companies", "name": "Ver empresas",    "slug": "companies.view",   "description": "Consultar empresas registradas."},
    {"module": "companies", "name": "Crear empresa",   "slug": "companies.create", "description": "Registrar nuevas empresas."},
    {"module": "companies", "name": "Editar empresa",  "slug": "companies.edit",   "description": "Modificar datos de empresas."},
    {"module": "companies", "name": "Eliminar empresa","slug": "companies.delete", "description": "Archivar empresas."},
    # Usuarios
    {"module": "users", "name": "Ver usuarios",    "slug": "users.view",   "description": "Consultar usuarios y membresías."},
    {"module": "users", "name": "Crear usuario",   "slug": "users.create", "description": "Crear usuarios dentro de una empresa."},
    {"module": "users", "name": "Editar usuario",  "slug": "users.edit",   "description": "Editar datos de usuarios."},
    {"module": "users", "name": "Eliminar usuario","slug": "users.delete", "description": "Remover usuarios de una empresa."},
    # Roles
    {"module": "roles", "name": "Ver roles",    "slug": "roles.view",   "description": "Consultar roles del sistema."},
    {"module": "roles", "name": "Crear rol",    "slug": "roles.create", "description": "Crear nuevos roles."},
    {"module": "roles", "name": "Editar rol",   "slug": "roles.edit",   "description": "Modificar roles existentes."},
    {"module": "roles", "name": "Eliminar rol", "slug": "roles.delete", "description": "Eliminar roles."},
    # Permisos
    {"module": "permissions", "name": "Ver permisos",   "slug": "permissions.view",   "description": "Consultar permisos."},
    {"module": "permissions", "name": "Crear permiso",  "slug": "permissions.create", "description": "Crear nuevos permisos."},
    {"module": "permissions", "name": "Asignar permisos","slug": "permissions.assign","description": "Asignar permisos a roles."},
    # Sucursales
    {"module": "branches", "name": "Ver sucursales",    "slug": "branches.view",   "description": "Consultar sucursales."},
    {"module": "branches", "name": "Crear sucursal",    "slug": "branches.create", "description": "Registrar nuevas sucursales."},
    {"module": "branches", "name": "Editar sucursal",   "slug": "branches.edit",   "description": "Modificar sucursales."},
    {"module": "branches", "name": "Eliminar sucursal", "slug": "branches.delete", "description": "Desactivar sucursales."},
    # Productos
    {"module": "products", "name": "Ver productos",    "slug": "products.view",   "description": "Consultar catálogo de productos."},
    {"module": "products", "name": "Crear producto",   "slug": "products.create", "description": "Registrar productos."},
    {"module": "products", "name": "Editar producto",  "slug": "products.edit",   "description": "Editar productos."},
    {"module": "products", "name": "Eliminar producto","slug": "products.delete", "description": "Desactivar productos."},
    # Reportes
    {"module": "reports", "name": "Ver reportes",     "slug": "reports.view",   "description": "Acceder a reportes."},
    {"module": "reports", "name": "Exportar reportes","slug": "reports.export", "description": "Exportar reportes."},
    # Auditoría
    {"module": "audit", "name": "Ver auditoría", "slug": "audit.view", "description": "Consultar logs de auditoría."},
)

SYSTEM_ROLES: tuple[dict[str, Any], ...] = (
    {
        "name": "super_admin",
        "description": "Acceso total global.",
        "level": 1000,
        "is_system": True,
    },
    {
        "name": "tenant_admin",
        "description": "Administra su tenant.",
        "level": 900,
        "is_system": True,
    },
    {
        "name": "branch_manager",
        "description": "Gestiona una sucursal.",
        "level": 500,
        "is_system": False,
    },
    {
        "name": "sales_agent",
        "description": "Crea ordenes de venta.",
        "level": 200,
        "is_system": False,
    },
    {
        "name": "warehouse",
        "description": "Gestiona inventario.",
        "level": 200,
        "is_system": False,
    },
    {
        "name": "accountant",
        "description": "Acceso a contabilidad.",
        "level": 200,
        "is_system": False,
    },
    {
        "name": "viewer",
        "description": "Solo lectura.",
        "level": 50,
        "is_system": False,
    },
)

ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "super_admin": tuple(p["slug"] for p in PERMISSIONS),
    "tenant_admin": (
        "companies.view", "companies.edit",
        "users.view", "users.create", "users.edit", "users.delete",
        "roles.view", "roles.create", "roles.edit", "roles.delete",
        "permissions.view", "permissions.create", "permissions.assign",
        "branches.view", "branches.create", "branches.edit", "branches.delete",
        "products.view", "products.create", "products.edit", "products.delete",
        "reports.view", "reports.export",
        "audit.view",
    ),
    "branch_manager": (
        "users.view", "users.create", "users.edit",
        "branches.view",
        "products.view", "products.create", "products.edit",
        "reports.view",
    ),
    "sales_agent": (
        "products.view",
        "branches.view",
        "reports.view",
    ),
    "warehouse": (
        "products.view", "products.create", "products.edit",
        "branches.view",
        "reports.view",
    ),
    "accountant": (
        "users.view",
        "products.view",
        "branches.view",
        "reports.view", "reports.export",
        "audit.view",
    ),
    "viewer": (
        "companies.view",
        "users.view",
        "branches.view",
        "products.view",
        "reports.view",
    ),
}

DEMO_TENANT = {
    "name": "Inversiones Demo, C.A.",
    "slug": "empresa-demo",
    "rif": "J-50000001-1",
    "address": "Av. Principal de Caracas, Torre Demo, Piso 4",
    "location": "Caracas, VE",
    "phone": "+58-212-555-0101",
    "email": "admin@empresa-demo.com",
    "plan": "enterprise",
    "settings": '{"currency":"VES","timezone":"America/Caracas"}',
}

DEMO_USERS: tuple[dict[str, str | None], ...] = (
    {
        "username": "superadmin",
        "email": "superadmin@contabcloud.dev",
        "password": "superadmin123",
        "first_name": "Super",
        "first_lastname": "Admin",
        "phone": "+58-412-000-0001",
        "global_role": "super_admin",
        "tenant_role": "tenant_admin",
    },
    {
        "username": "admin_empresa",
        "email": "admin@empresa-demo.com",
        "password": "admin123",
        "first_name": "Ana",
        "first_lastname": "Admin",
        "phone": "+58-412-000-0002",
        "global_role": None,
        "tenant_role": "tenant_admin",
    },
    {
        "username": "contador_demo",
        "email": "contador@empresa-demo.com",
        "password": "contador123",
        "first_name": "Carlos",
        "first_lastname": "Contador",
        "phone": "+58-412-000-0003",
        "global_role": None,
        "tenant_role": "accountant",
    },
    {
        "username": "cliente_lectura",
        "email": "cliente@empresa-demo.com",
        "password": "cliente123",
        "first_name": "Claudia",
        "first_lastname": "Consulta",
        "phone": "+58-412-000-0004",
        "global_role": None,
        "tenant_role": "viewer",
    },
)


def _validate_catalog() -> None:
    permission_slugs = {permission["slug"] for permission in PERMISSIONS}
    role_names = {role["name"] for role in SYSTEM_ROLES}

    for role_name, slugs in ROLE_PERMISSIONS.items():
        unknown_slugs = sorted(set(slugs) - permission_slugs)
        if unknown_slugs:
            raise ValueError(f"Permisos no definidos para el rol {role_name}: {unknown_slugs}")

    for user in DEMO_USERS:
        global_role = user["global_role"]
        tenant_role = user["tenant_role"]
        if global_role and global_role not in role_names:
            raise ValueError(f"Rol global no definido en seed: {global_role}")
        if tenant_role and tenant_role not in role_names:
            raise ValueError(f"Rol tenant no definido en seed: {tenant_role}")


_validate_catalog()


def get_seed_permission_slugs() -> set[str]:
    return {permission["slug"] for permission in PERMISSIONS}


def _ensure_roles(cur) -> dict[str, str]:
    role_ids: dict[str, str] = {}
    for role in SYSTEM_ROLES:
        cur.execute(
            """
            INSERT INTO global.roles (name, description, level, is_system)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (name)
            DO UPDATE SET
                description = EXCLUDED.description,
                level = EXCLUDED.level,
                is_system = EXCLUDED.is_system,
                deleted_at = NULL
            RETURNING uuid::text AS id, name
            """,
            (role["name"], role["description"], role["level"], role["is_system"]),
        )
        row = cur.fetchone()
        role_ids[row["name"]] = row["id"]
    return role_ids


def _ensure_permissions(cur) -> dict[str, str]:
    permission_ids: dict[str, str] = {}
    for permission in PERMISSIONS:
        cur.execute(
            """
            INSERT INTO global.permissions (module, name, slug, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (slug)
            DO UPDATE SET
                module = EXCLUDED.module,
                name = EXCLUDED.name,
                description = EXCLUDED.description
            RETURNING uuid::text AS id, slug
            """,
            (
                permission["module"],
                permission["name"],
                permission["slug"],
                permission["description"],
            ),
        )
        row = cur.fetchone()
        permission_ids[row["slug"]] = row["id"]
    return permission_ids


def _ensure_role_permissions(cur, role_ids: dict[str, str], permission_ids: dict[str, str]) -> None:
    for role_name, permission_slugs in ROLE_PERMISSIONS.items():
        role_id = role_ids[role_name]
        for permission_slug in permission_slugs:
            cur.execute(
                """
                INSERT INTO global.role_permissions (role_id, permission_id)
                VALUES (%s::uuid, %s::uuid)
                ON CONFLICT (role_id, permission_id) DO NOTHING
                """,
                (role_id, permission_ids[permission_slug]),
            )


def _ensure_demo_tenant(cur) -> dict[str, str]:
    cur.execute(
        """
        INSERT INTO global.tenants (
            name,
            slug,
            rif,
            address,
            location,
            phone,
            email,
            status,
            plan,
            settings
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', %s, %s)
        ON CONFLICT (slug)
        DO UPDATE SET
            name = EXCLUDED.name,
            rif = EXCLUDED.rif,
            address = EXCLUDED.address,
            location = EXCLUDED.location,
            phone = EXCLUDED.phone,
            email = EXCLUDED.email,
            status = 'active',
            plan = EXCLUDED.plan,
            settings = EXCLUDED.settings,
            deleted_at = NULL,
            updated_at = NOW()
        RETURNING uuid::text AS id, slug, schema_name
        """,
        (
            DEMO_TENANT["name"],
            DEMO_TENANT["slug"],
            DEMO_TENANT["rif"],
            DEMO_TENANT["address"],
            DEMO_TENANT["location"],
            DEMO_TENANT["phone"],
            DEMO_TENANT["email"],
            DEMO_TENANT["plan"],
            DEMO_TENANT["settings"],
        ),
    )
    tenant = cur.fetchone()
    cur.execute("CALL global.sp_create_tenant_schema(%s)", (tenant["slug"],))
    return tenant


def _ensure_demo_user(cur, user_data: dict[str, str | None]) -> dict[str, str]:
    cur.execute(
        """
        INSERT INTO global.users (
            username,
            email,
            password_hash,
            status,
            email_verified_at
        )
        VALUES (%s, %s, %s, 'active', NOW())
        ON CONFLICT (email)
        DO UPDATE SET
            username = EXCLUDED.username,
            password_hash = EXCLUDED.password_hash,
            status = 'active',
            email_verified_at = COALESCE(global.users.email_verified_at, EXCLUDED.email_verified_at),
            deleted_at = NULL,
            updated_at = NOW()
        RETURNING uuid::text AS id, email
        """,
        (
            user_data["username"],
            user_data["email"],
            hash_password(str(user_data["password"])),
        ),
    )
    user = cur.fetchone()

    cur.execute(
        """
        INSERT INTO global.profiles (user_id, first_name, first_lastname, phone)
        VALUES (%s::uuid, %s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET
            first_name = EXCLUDED.first_name,
            first_lastname = EXCLUDED.first_lastname,
            phone = EXCLUDED.phone,
            updated_at = NOW()
        """,
        (
            user["id"],
            user_data["first_name"],
            user_data["first_lastname"],
            user_data["phone"],
        ),
    )
    return user


def _ensure_user_global_role(cur, user_id: str, role_id: str) -> None:
    cur.execute(
        """
        INSERT INTO global.user_global_roles (user_id, role_id)
        VALUES (%s::uuid, %s::uuid)
        ON CONFLICT (user_id, role_id)
        DO UPDATE SET
            revoked_at = NULL,
            revoked_by = NULL
        """,
        (user_id, role_id),
    )


def _ensure_user_tenant_membership(cur, user_id: str, tenant_id: str, invited_by: str | None) -> None:
    cur.execute(
        """
        INSERT INTO global.user_tenants (user_id, tenant_id, is_active, invited_by, joined_at)
        VALUES (%s::uuid, %s::uuid, TRUE, %s::uuid, NOW())
        ON CONFLICT (user_id, tenant_id)
        DO UPDATE SET
            is_active = TRUE,
            invited_by = EXCLUDED.invited_by,
            joined_at = COALESCE(global.user_tenants.joined_at, EXCLUDED.joined_at)
        """,
        (user_id, tenant_id, invited_by),
    )


def _ensure_user_tenant_role(
    cur,
    user_id: str,
    tenant_id: str,
    role_id: str,
    assigned_by: str | None,
) -> None:
    cur.execute(
        """
        SELECT uuid::text AS id
        FROM global.user_tenant_roles
        WHERE user_id = %s::uuid
          AND tenant_id = %s::uuid
          AND role_id = %s::uuid
          AND branch_id IS NULL
        LIMIT 1
        """,
        (user_id, tenant_id, role_id),
    )
    existing = cur.fetchone()
    if existing:
        cur.execute(
            """
            UPDATE global.user_tenant_roles
            SET assigned_by = %s::uuid,
                revoked_at = NULL,
                revoked_by = NULL
            WHERE uuid = %s::uuid
            """,
            (assigned_by, existing["id"]),
        )
        return

    cur.execute(
        """
        INSERT INTO global.user_tenant_roles (user_id, tenant_id, role_id, assigned_by)
        VALUES (%s::uuid, %s::uuid, %s::uuid, %s::uuid)
        """,
        (user_id, tenant_id, role_id, assigned_by),
    )


def _ensure_demo_branch(cur, tenant_id: str, schema_name: str) -> None:
    insert_branch = sql.SQL(
        """
        INSERT INTO {}.branches (tenant_id, name, address, is_active)
        SELECT %s::uuid, %s, %s, TRUE
        WHERE NOT EXISTS (
            SELECT 1
            FROM {}.branches
            WHERE tenant_id = %s::uuid
              AND name = %s
        )
        """
    ).format(sql.Identifier(schema_name), sql.Identifier(schema_name))
    cur.execute(
        insert_branch,
        (
            tenant_id,
            "Casa Matriz",
            DEMO_TENANT["address"],
            tenant_id,
            "Casa Matriz",
        ),
    )


def ensure_seed_data(conn) -> dict[str, Any]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        role_ids = _ensure_roles(cur)
        permission_ids = _ensure_permissions(cur)
        _ensure_role_permissions(cur, role_ids, permission_ids)
        tenant = _ensure_demo_tenant(cur)
        _ensure_demo_branch(cur, tenant["id"], tenant["schema_name"])

        created_users: list[dict[str, str]] = []
        super_admin_user_id: str | None = None

        for user_data in DEMO_USERS:
            user = _ensure_demo_user(cur, user_data)
            created_users.append(
                {
                    "email": str(user_data["email"]),
                    "password": str(user_data["password"]),
                    "tenant_role": str(user_data["tenant_role"]),
                }
            )
            if user_data["global_role"] == "super_admin":
                super_admin_user_id = user["id"]
                _ensure_user_global_role(cur, user["id"], role_ids["super_admin"])

        for user_data in DEMO_USERS:
            cur.execute(
                "SELECT uuid::text AS id FROM global.users WHERE email = %s",
                (user_data["email"],),
            )
            user = cur.fetchone()
            _ensure_user_tenant_membership(cur, user["id"], tenant["id"], super_admin_user_id)
            _ensure_user_tenant_role(
                cur,
                user["id"],
                tenant["id"],
                role_ids[str(user_data["tenant_role"])],
                super_admin_user_id,
            )

    conn.commit()
    return {
        "tenant": tenant,
        "users": created_users,
        "permissions_count": len(permission_ids),
        "roles_count": len(role_ids),
    }


def run_seed() -> dict[str, Any]:
    from app.database import get_connection, init_db_migrations, release_connection

    init_db_migrations()

    conn = get_connection()
    try:
        summary = ensure_seed_data(conn)
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)

    print("Seed ejecutado correctamente.")
    print(
        f"Tenant demo: {summary['tenant']['slug']} ({summary['tenant']['id']}) "
        f"- permisos: {summary['permissions_count']} - roles: {summary['roles_count']}"
    )
    print("Credenciales demo:")
    for user in summary["users"]:
        print(f"- {user['email']} / {user['password']} ({user['tenant_role']})")
    return summary


if __name__ == "__main__":
    run_seed()
