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


def init_db_from_sql():
    # Compatibilidad hacia atras con llamadas existentes.
    init_db_migrations()


if __name__ == "__main__":
    init_db_migrations()