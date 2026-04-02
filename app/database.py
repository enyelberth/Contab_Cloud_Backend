import os
from pathlib import Path
import hashlib

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://enyelberth:30204334@localhost:5432/erp",
)

_pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL,
)


def get_connection():
    return _pool.getconn()


def release_connection(conn):
    _pool.putconn(conn)


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        release_connection(conn)


def fetch_one(conn, query, params=None):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params or ())
        return cur.fetchone()


def fetch_all(conn, query, params=None):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params or ())
        return cur.fetchall()


def execute(conn, query, params=None, returning=False):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params or ())
        row = cur.fetchone() if returning else None
    conn.commit()
    return row


def execute_all(conn, query, params=None):
    """Ejecuta un INSERT/UPDATE con RETURNING y devuelve todas las filas resultantes."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params or ())
        rows = cur.fetchall()
    conn.commit()
    return rows


def execute_script(conn, script):
    with conn.cursor() as cur:
        cur.execute(script)
    conn.commit()


def _ensure_schema_migrations(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(32) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    conn.commit()


def _apply_migration_file(conn, version: str, file_path: Path):
    script = file_path.read_text(encoding="utf-8")
    checksum = hashlib.sha256(script.encode("utf-8")).hexdigest()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT version, checksum FROM schema_migrations WHERE version = %s", (version,))
        row = cur.fetchone()
        if row:
            if row["checksum"] != checksum:
                raise RuntimeError(
                    f"Checksum no coincide para migracion {version} ({file_path.name}). "
                    "No modifiques migraciones aplicadas."
                )
            return False

    with conn.cursor() as cur:
        cur.execute(script)
        cur.execute(
            """
            INSERT INTO schema_migrations (version, name, checksum)
            VALUES (%s, %s, %s)
            """,
            (version, file_path.name, checksum),
        )
    conn.commit()
    return True


def init_db_migrations():
    migrations_dir = Path(__file__).resolve().parent.parent / "db" / "migrations"
    if not migrations_dir.exists():
        raise FileNotFoundError(f"No existe el directorio de migraciones: {migrations_dir}")

    conn = get_connection()
    try:
        _ensure_schema_migrations(conn)

        applied = 0
        migration_files = sorted(migrations_dir.glob("*.sql"))
        for file_path in migration_files:
            version = file_path.name.split("_", 1)[0]
            if _apply_migration_file(conn, version, file_path):
                applied += 1

        print(f"Conexion PostgreSQL OK. Migraciones aplicadas: {applied}")
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def crear_schema_empresa(conn, company_id: int) -> None:
    """Crea el schema de PostgreSQL y todas las tablas contables para una empresa nueva.

    Debe llamarse justo después de insertar la empresa en la tabla `companies`.
    El nombre del schema se construye como empresa_{company_id}.
    Ejemplo: company_id=5 → schema 'empresa_5'.
    """
    schema = f"empresa_{int(company_id)}"  # int() previene SQL injection
    script = f"""
        CREATE SCHEMA IF NOT EXISTS {schema};

        -- Tabla de prueba / sandbox
        CREATE TABLE IF NOT EXISTS {schema}.prueba (
            id          SERIAL PRIMARY KEY,
            nombre      VARCHAR(100) NOT NULL,
            descripcion TEXT,
            created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Catálogo de cuentas (Plan de Cuentas)
        CREATE TABLE IF NOT EXISTS {schema}.cont_cuentas (
            id                  SERIAL,
            txt_cuenta          VARCHAR(50)  NOT NULL,
            txt_denominacion    VARCHAR(150),
            txt_nom_corto       VARCHAR(50),
            num_nivel           INT,
            txt_status          VARCHAR(50),
            txt_comentario      VARCHAR(200) DEFAULT '',
            cuenta_padre        VARCHAR(50),
            nomb_cuenta_padre   VARCHAR(80),
            num_tipo_aux        INT          DEFAULT -1,
            tipo_aux            VARCHAR(50)  DEFAULT '',
            num_tipo_cuenta     INT          DEFAULT -1,
            cod_tipo_aux        VARCHAR(10)  DEFAULT '',
            num_aux             INT          DEFAULT -1,
            PRIMARY KEY (txt_cuenta)
        );
    """
    execute_script(conn, script)


def init_db_from_sql():
    # Compatibilidad hacia atras con llamadas existentes.
    init_db_migrations()


if __name__ == "__main__":
    init_db_migrations()