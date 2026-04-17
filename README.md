# Contab Cloud — Backend API

API REST construida con FastAPI y PostgreSQL (SQL puro, sin ORM).
Arquitectura multi-tenant con un schema de PostgreSQL por empresa.

---

## Stack

- Python 3.10+
- FastAPI 0.135.1
- Uvicorn 0.42.0
- psycopg2-binary (conexion sincrona a PostgreSQL)
- Pydantic 2.12.5 (validacion de datos)
- PyJWT + passlib[bcrypt] (autenticacion)
- PostgreSQL 15 (Docker)

---

## Levantar el entorno

### Con Docker (recomendado)

```bash
docker compose up -d
```

Servicios:
- PostgreSQL en `:5432`
- Adminer (UI web BD) en `:8080`

### Manual

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Variables en `.env`:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/kaizen
DB_USER=usuario
DB_PASSWORD=password
DB_NAME=kaizen
```

Correr la API:

```bash
uvicorn app.main:app --reload
```

URLs:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Seed — Datos Iniciales

```bash
python seed.py
```

Crea la empresa demo y estos usuarios:

| Email | Password | Rol |
|-------|----------|-----|
| `superadmin@contabcloud.dev` | `superadmin123` | super_admin + tenant_admin |
| `admin@empresa-demo.com` | `admin123` | tenant_admin |
| `contador@empresa-demo.com` | `contador123` | accountant |
| `cliente@empresa-demo.com` | `cliente123` | viewer |

---

## Migraciones

Las migraciones SQL se aplican automaticamente al iniciar la app.
Archivos en `db/migrations/` con formato `<version>_<descripcion>.sql`.

```bash
python -m app.migrate status   # ver estado
python -m app.migrate up       # aplicar pendientes
```

---

## Endpoints Implementados

### Autenticacion — `/auth`

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/auth/login` | Login → access_token + refresh_token |
| POST | `/auth/refresh` | Renovar access_token |
| POST | `/auth/logout` | Invalidar sesion |
| GET | `/auth/me` | Datos del usuario actual (incluye `tenant_id`) |

### Empresas — `/companies`

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/companies/` | Listar (skip/limit) |
| POST | `/companies/` | Crear empresa |
| GET | `/companies/{id}` | Obtener empresa |
| PUT | `/companies/{id}` | Actualizar |
| DELETE | `/companies/{id}` | Eliminar |

### Plan de Cuentas — `/companies/{company_id}/cuentas`

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/companies/{id}/cuentas` | Listar todas las cuentas |
| POST | `/companies/{id}/cuentas` | Crear cuenta |
| GET | `/companies/{id}/cuentas/{codigo}` | Obtener por codigo |
| PUT | `/companies/{id}/cuentas/{codigo}` | Actualizar cuenta |
| DELETE | `/companies/{id}/cuentas/{codigo}` | Eliminar cuenta |
| GET | `/companies/{id}/cuentas/comparar` | Comparar plan entre dos empresas |
| POST | `/companies/{id}/cuentas/importar` | Importar plan (modo: omitir/reemplazar) |
| POST | `/companies/{id}/cuentas/lote` | Crear multiples cuentas en lote |

Campos del schema `CuentaCreate`:
- `txt_cuenta` (str, requerido) — codigo de cuenta
- `txt_denominacion` — nombre completo
- `txt_nom_corto` — nombre corto
- `num_nivel` — nivel jerarquico
- `txt_status` — estado (A=Activa, I=Inactiva)
- `txt_comentario` — comentario
- `cuenta_padre` — codigo de la cuenta padre

### Comprobantes — `/companies/{company_id}/comprobantes`

#### Maestro (cabecera)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/companies/{id}/comprobantes` | Listar comprobantes |
| POST | `/companies/{id}/comprobantes` | Crear (puede incluir detalles en el body) |
| GET | `/companies/{id}/comprobantes/{num}` | Obtener con sus lineas |
| PUT | `/companies/{id}/comprobantes/{num}` | Actualizar cabecera |
| DELETE | `/companies/{id}/comprobantes/{num}` | Eliminar |

Campos del schema `MaestroComprobanteCreate`:
- `fecha_comprobante` — fecha del asiento
- `tipo` — tipo (D=Diario, C=Compras, V=Ventas, B=Banco, N=Nomina, ...)
- `txt_descripcion` — descripcion general
- `txt_status` — estado (A=Activo, AN=Anulado)
- `sg_moneda` — moneda (Bs, USD, EUR)
- `detalles` — lista opcional de lineas al crear

#### Detalles (lineas de partida doble)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/companies/{id}/comprobantes/{num}/detalles` | Listar lineas |
| POST | `/companies/{id}/comprobantes/{num}/detalles` | Agregar linea |
| GET | `/companies/{id}/comprobantes/{num}/detalles/{det_id}` | Obtener linea |
| PUT | `/companies/{id}/comprobantes/{num}/detalles/{det_id}` | Actualizar linea |
| DELETE | `/companies/{id}/comprobantes/{num}/detalles/{det_id}` | Eliminar linea |

Campos del schema `DetalleComprobanteCreate`:
- `txt_cuenta` (str, requerido) — codigo de cuenta
- `txt_concepto` — descripcion de la linea
- `num_debito` — monto debito (Decimal, default 0)
- `num_credito` — monto credito (Decimal, default 0)
- `num_item` — numero de linea
- `txt_referencia`, `txt_tipo`, `fecha`, `auxiliar`

### Ejercicios Fiscales — `/companies/{company_id}/ejercicios`

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/companies/{id}/ejercicios` | Listar ejercicios |
| POST | `/companies/{id}/ejercicios` | Crear ejercicio + genera 12 meses automaticamente |
| GET | `/companies/{id}/ejercicios/{ej_id}` | Obtener ejercicio |
| PUT | `/companies/{id}/ejercicios/{ej_id}` | Actualizar |
| DELETE | `/companies/{id}/ejercicios/{ej_id}` | Eliminar |

La respuesta de creacion incluye `{ ejercicio, meses_creados: [12 meses] }`.

Campos del schema `EjercicioCreate`:
- `ano` (str, requerido) — año fiscal, ej. "2026"
- `fecha_i` — fecha inicio
- `fecha_f` — fecha fin
- `obser` — observaciones
- `status` — estado (A=Abierto, C=Cerrado, I=Inactivo)
- `bloqueo` — "0"=libre, "1"=bloqueado

### Meses Contables — `/companies/{company_id}/meses`

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/companies/{id}/meses` | Listar meses |
| POST | `/companies/{id}/meses` | Crear mes |
| GET | `/companies/{id}/meses/{mes_id}` | Obtener mes |
| PUT | `/companies/{id}/meses/{mes_id}` | Actualizar (cambiar estado/bloqueo) |
| DELETE | `/companies/{id}/meses/{mes_id}` | Eliminar |

Campos del schema `MesCreate`:
- `mes` (str) — nombre del mes, ej. "Enero"
- `ano` (str) — año, ej. "2026"
- `n_mes_contble` — numero mes contable (1-12)
- `n_mes_sistema` — numero mes sistema
- `ejercicio` — codigo del ejercicio
- `status` — "1"=Abierto, "2"=En proceso, "3"=Cerrado, "4"=Inactivo
- `bloqueo` — "0"=libre, "1"=bloqueado
- `fecha_i`, `fecha_f` — rango del mes
- `fecha_cierre`, `fecha_creado`, `tipo`, `usuario`

### Usuarios, Roles y Permisos

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET/POST/PUT/DELETE | `/sales/users` | CRUD de usuarios |
| GET/POST | `/roles` | CRUD de roles |
| GET/POST/DELETE | `/permissions` | CRUD de permisos |
| POST | `/permissions/assign` | Asignar permiso a rol |
| GET/POST/PUT/DELETE | `/branches` | CRUD de sedes/sucursales |

---

## Estructura del Proyecto

```
app/
├── main.py              # Instancia FastAPI, registro de routers, middleware
├── database.py          # Pool de conexiones PostgreSQL, sistema de migraciones
├── audit.py             # Registro de audit trail
├── request_context.py   # Metadata de request (request_id, IP, endpoint)
├── auth/                # Autenticacion JWT
│   ├── router.py
│   ├── schemas.py
│   ├── service.py
│   ├── security.py      # JWT y bcrypt
│   └── dependencies.py  # get_current_user, require_permission
├── company/             # Gestion multi-tenant de empresas
├── cuentas/             # Plan de cuentas (schema tenant)
├── comprobantes/        # Asientos contables maestro + detalles
├── ejercicio/           # Ejercicios fiscales
├── meses/               # Periodos mensuales
├── user/                # Gestion de usuarios
├── role/                # Gestion de roles
├── permissions/         # Gestion de permisos
├── branche/             # Sedes/sucursales
└── product/             # Catalogo de productos
db/
└── migrations/          # SQL versionado (001_init... a 006_add_cont_comprobantes.sql)
```

---

## Sistema de Permisos

Los endpoints contables usan `require_permission()` con permisos por recurso:

```python
# Ejemplos de permisos usados
"cuentas.view"        "cuentas.create"       "cuentas.delete"
"comprobantes.view"   "comprobantes.create"  "comprobantes.edit"
"meses.view"          "meses.edit"
"ejercicio.view"      "ejercicio.create"
```

El frontend lee los menus y permisos dinamicamente desde:
- `frontend_menus` — estructura del menu
- `role_menu_access` — que puede ver/hacer cada rol
- `app_modules` — modulos de la aplicacion

---

## Reglas de Negocio

1. Solo cuentas con `permite_movimiento = true` aceptan lineas de comprobante
2. `Σ debito = Σ credito` — obligatorio para contabilizar (partida doble)
3. Solo un periodo `abierto` por ejercicio al mismo tiempo
4. Para cerrar un periodo: no deben existir comprobantes en `borrador`
5. La anulacion genera comprobante inverso — nunca elimina fisicamente
6. Para anular: periodo `abierto` Y ejercicio `activo` (ambas condiciones)
7. Reapertura de periodo `auditado`: solo rol `FIRM_OWNER` + motivo en audit trail
8. No pueden existir dos ejercicios con el mismo año para la misma empresa

---

## Troubleshooting

- **Error de conexion PostgreSQL:** revisar que el contenedor este activo y las credenciales en `.env`
- **Puerto ocupado (8000 o 5432):** liberar el puerto o cambiar configuracion
- **Migracion fallida:** revisar `public.schema_migrations` para ver cual migracion fallo y su checksum
