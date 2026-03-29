import os
from pathlib import Path

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


def init_db_from_sql():
    sql_path = Path(__file__).resolve().parent.parent / "sql.txt"
    if not sql_path.exists():
        raise FileNotFoundError(f"No existe el archivo SQL: {sql_path}")

    conn = get_connection()
    try:
        existing = fetch_one(conn, "SELECT to_regclass('public.branches') AS table_name")
        if existing and existing.get("table_name"):
            print("Esquema ya existe, se omite inicializacion desde sql.txt")
            return

        script = sql_path.read_text(encoding="utf-8")
        execute_script(conn, script)
        print("Conexion PostgreSQL OK y esquema aplicado desde sql.txt")
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


if __name__ == "__main__":
    init_db_from_sql()