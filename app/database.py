import os
from pathlib import Path
import hashlib
from typing import Dict, List

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


def _migrations_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "db" / "migrations"


def _migration_version(file_path: Path) -> str:
    return file_path.name.split("_", 1)[0]


def _file_checksum(file_path: Path) -> str:
    script = file_path.read_text(encoding="utf-8")
    return hashlib.sha256(script.encode("utf-8")).hexdigest()


def get_migration_status() -> List[Dict[str, str]]:
    migrations_dir = _migrations_dir()
    if not migrations_dir.exists():
        raise FileNotFoundError(f"No existe el directorio de migraciones: {migrations_dir}")

    conn = get_connection()
    try:
        _ensure_schema_migrations(conn)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT version, checksum, applied_at FROM schema_migrations")
            rows = cur.fetchall()

        applied_by_version = {row["version"]: row for row in rows}
        status_rows = []

        for file_path in sorted(migrations_dir.glob("*.sql")):
            version = _migration_version(file_path)
            checksum = _file_checksum(file_path)
            applied = applied_by_version.get(version)

            if not applied:
                status_rows.append(
                    {
                        "version": version,
                        "name": file_path.name,
                        "state": "pending",
                        "applied_at": "",
                    }
                )
                continue

            state = "applied" if applied["checksum"] == checksum else "checksum_mismatch"
            status_rows.append(
                {
                    "version": version,
                    "name": file_path.name,
                    "state": state,
                    "applied_at": str(applied["applied_at"]),
                }
            )

        return status_rows
    finally:
        release_connection(conn)


def run_db_migrations() -> int:
    migrations_dir = _migrations_dir()
    if not migrations_dir.exists():
        raise FileNotFoundError(f"No existe el directorio de migraciones: {migrations_dir}")

    conn = get_connection()
    try:
        _ensure_schema_migrations(conn)

        applied = 0
        migration_files = sorted(migrations_dir.glob("*.sql"))
        for file_path in migration_files:
            version = _migration_version(file_path)
            if _apply_migration_file(conn, version, file_path):
                applied += 1

        return applied
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def init_db_migrations():
    try:
        applied = run_db_migrations()
        print(f"Conexion PostgreSQL OK. Migraciones aplicadas: {applied}")
    except Exception:
        raise


def init_db_from_sql():
    # Compatibilidad hacia atras con llamadas existentes.
    init_db_migrations()


if __name__ == "__main__":
    init_db_migrations()