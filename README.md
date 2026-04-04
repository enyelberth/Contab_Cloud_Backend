# Contab Cloud Backend

Backend API para ERP multi-sede construido con FastAPI y PostgreSQL usando SQL puro (sin ORM).

## Stack

- Python 3.10+
- FastAPI
- Uvicorn
- psycopg2-binary
- PostgreSQL
- Docker Compose (PostgreSQL + Adminer)

## Requisitos

- Python 3.10 o superior
- pip
- Docker y Docker Compose (opcional, recomendado para base de datos local)

## Instalacion local

1. Crear entorno virtual:

```bash
python -m venv venv
```

2. Activar entorno virtual:

```bash
source venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Configuracion de entorno

Configura variables en [.env](.env):

- `DATABASE_URL`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

Ejemplo:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/kaizen
DB_USER=usuario
DB_PASSWORD=password_seguro
DB_NAME=kaizen
```

## Levantar base de datos con Docker

```bash
docker compose up -d
```

Servicios definidos en [docker-compose.yml](docker-compose.yml):

- PostgreSQL en `5432`
- Adminer en `8080`

## Ejecutar API

Con el entorno virtual activo:

```bash
uvicorn app.main:app --reload
```

API disponible en:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## Endpoints base

- `GET /`
- `GET/POST/PUT/DELETE /branches`
- `GET/POST/PUT/DELETE /sales/users`
- `GET/POST/PUT/DELETE /roles`
- `GET/POST/DELETE /permissions`
- `POST /permissions/assign`

Nota: al iniciar, la aplicacion aplica migraciones SQL versionadas desde `db/migrations`.

## Migraciones PostgreSQL

Comandos disponibles:

```bash
python -m app.migrate status
python -m app.migrate up
```

Convencion de archivos:

- Carpeta: `db/migrations`
- Formato: `<version>_<descripcion>.sql`
- Ejemplo: `001_init_enterprise.sql`

La tabla de control de migraciones es `public.schema_migrations` y se crea automaticamente.

## Seed inicial

Para cargar datos base:

```bash
python seed.py
```

El script aplica migraciones SQL (tablas + permisos + menus + datos demo idempotentes).

Datos demo creados automaticamente:

- Empresa demo: `Inversiones Demo, C.A.` (`J-50000001-1`)
- Usuarios:
  - `superadmin@contabcloud.dev` (SUPER_ADMIN)
  - `contador@empresa-demo.com` (ADMIN_EMPRESA)
  - `asistente@empresa-demo.com` (CONTADOR)
  - `cliente@empresa-demo.com` (CLIENTE_LECTURA)

Nota: los `password_hash` son de prueba para desarrollo local.

## Menus y permisos por rol (frontend)

El frontend debe leer menus y permisos desde BD:

- Menus: `frontend_menus`
- Modulos: `app_modules`
- Matriz de acceso por rol/menu: `role_menu_access`
- Reglas de delegacion de roles/permisos: `role_delegation_rules`

Cada menu trae banderas para UI y acciones:

- `can_view`
- `can_create`
- `can_update`
- `can_delete`
- `can_assign_permissions`

## Estructura principal

- [app/main.py](app/main.py): instancia FastAPI y registro de routers
- [app/database.py](app/database.py): conexion y sesion de base de datos
- [db/migrations](db/migrations): migraciones SQL versionadas
- [app/branche](app/branche): modulo de sedes
- [app/user](app/user): modulo de usuarios
- [app/role](app/role): modulo de roles
- [app/permissions](app/permissions): modulo de permisos
- [seed.py](seed.py): carga de datos iniciales

## Seguridad

- No subas credenciales reales al repositorio.
- Usa valores diferentes por entorno (dev/staging/prod).
- Mantem `DATABASE_URL` fuera de control de versiones en produccion.

## Troubleshooting

- Error de conexion a PostgreSQL:
  revisa contenedor activo y credenciales en [.env](.env).
- Puerto ocupado (`8000` o `5432`):
  libera el puerto o cambia configuracion local.
