from fastapi import HTTPException

from app.database import execute, fetch_all
from app.prueba.schemas import PruebaCreate


def _schema(company_id: int) -> str:
    """Construye el nombre del schema a partir del id de empresa.
    Castear a int garantiza que no haya SQL injection.
    Ejemplo: company_id=3 → 'empresa_3'
    """
    return f"empresa_{int(company_id)}"


def get_prueba(db, company_id: int):
    schema = _schema(company_id)
    try:
        return fetch_all(
            db,
            f"SELECT id, nombre, descripcion, created_at FROM {schema}.prueba ORDER BY id",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail=f"No existe el schema para la empresa con id={company_id}",
        )


def crear_prueba(db, company_id: int, data: PruebaCreate):
    schema = _schema(company_id)
    try:
        return execute(
            db,
            f"""
            INSERT INTO {schema}.prueba (nombre, descripcion)
            VALUES (%s, %s)
            RETURNING id, nombre, descripcion, created_at
            """,
            (data.nombre, data.descripcion),
            returning=True,
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail=f"No existe el schema para la empresa con id={company_id}",
        )
