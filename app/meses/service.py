from fastapi import HTTPException

from app.database import execute, execute_all, fetch_all, fetch_one
from app.meses.schemas import MesCreate, MesUpdate

_COLS = (
    "n_mes_contble, n_mes_sistema, mes, ano, status, bloqueo, "
    "ejercicio, tipo, usuario, fecha_i, fecha_f, fecha_cierre, fecha_creado"
)
_RETURNING = (
    "id, n_mes_contble, n_mes_sistema, mes, ano, status, bloqueo, "
    "ejercicio, tipo, usuario, fecha_i, fecha_f, fecha_cierre, fecha_creado"
)
_ROW_PH = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"


def _get_schema(db, company_id: str) -> str:
    row = fetch_one(
        db,
        "SELECT schema_name FROM global.tenants WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (company_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return row["schema_name"]


def _mes_params(m: MesCreate) -> tuple:
    return (
        m.n_mes_contble, m.n_mes_sistema, m.mes, m.ano, m.status,
        m.bloqueo, m.ejercicio, m.tipo, m.usuario,
        m.fecha_i, m.fecha_f, m.fecha_cierre, m.fecha_creado,
    )


def _not_found(mes_id: int):
    raise HTTPException(status_code=404, detail=f"Mes con id={mes_id} no encontrado")


# ------------------------------------------------------------------
# Listar todos los meses de una empresa
# ------------------------------------------------------------------
def get_meses(db, company_id: str):
    schema = _get_schema(db, company_id)
    try:
        return fetch_all(
            db,
            f"SELECT {_RETURNING} FROM {schema}.cont_meses_trab ORDER BY ano ASC, n_mes_contble ASC",
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al consultar los meses de trabajo")


# ------------------------------------------------------------------
# Obtener un mes por id
# ------------------------------------------------------------------
def get_mes(db, company_id: str, mes_id: int):
    schema = _get_schema(db, company_id)
    try:
        row = fetch_one(
            db,
            f"SELECT {_RETURNING} FROM {schema}.cont_meses_trab WHERE id = %s",
            (mes_id,),
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al consultar el mes")

    if not row:
        _not_found(mes_id)
    return row


# ------------------------------------------------------------------
# Crear un mes
# ------------------------------------------------------------------
def crear_mes(db, company_id: str, data: MesCreate):
    schema = _get_schema(db, company_id)
    try:
        return execute(
            db,
            f"INSERT INTO {schema}.cont_meses_trab ({_COLS}) VALUES {_ROW_PH} RETURNING {_RETURNING}",
            _mes_params(data),
            returning=True,
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el mes de trabajo")


# ------------------------------------------------------------------
# Actualizar un mes (solo los campos enviados)
# ------------------------------------------------------------------
def actualizar_mes(db, company_id: str, mes_id: int, data: MesUpdate):
    get_mes(db, company_id, mes_id)

    campos = data.model_dump(exclude_unset=True)
    if not campos:
        return get_mes(db, company_id, mes_id)

    schema = _get_schema(db, company_id)
    columnas = ", ".join(f"{col} = %s" for col in campos.keys())
    valores = list(campos.values()) + [mes_id]

    return execute(
        db,
        f"UPDATE {schema}.cont_meses_trab SET {columnas} WHERE id = %s RETURNING {_RETURNING}",
        valores,
        returning=True,
    )


# ------------------------------------------------------------------
# Eliminar un mes
# ------------------------------------------------------------------
def eliminar_mes(db, company_id: str, mes_id: int):
    get_mes(db, company_id, mes_id)
    schema = _get_schema(db, company_id)
    execute(db, f"DELETE FROM {schema}.cont_meses_trab WHERE id = %s", (mes_id,))
    return {"detail": f"Mes con id={mes_id} eliminado correctamente"}
