from datetime import date
from calendar import monthrange

from fastapi import HTTPException

from app.database import execute, execute_all, fetch_all, fetch_one
from app.ejercicio.schemas import EjercicioCreate, EjercicioUpdate

_COLS = "ano, fecha_i, fecha_f, obser, status, bloqueo"
_RETURNING = "id, ano, fecha_i, fecha_f, obser, status, bloqueo"

# Nombres de meses en español
_NOMBRES_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _get_schema(db, company_id: str) -> str:
    row = fetch_one(
        db,
        "SELECT schema_name FROM global.tenants WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (company_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return row["schema_name"]


def _not_found(ejercicio_id: int):
    raise HTTPException(status_code=404, detail=f"Ejercicio con id={ejercicio_id} no encontrado")


# ------------------------------------------------------------------
# Listar todos los ejercicios de una empresa
# ------------------------------------------------------------------
def get_ejercicios(db, company_id: str):
    schema = _get_schema(db, company_id)
    try:
        return fetch_all(
            db,
            f"SELECT {_RETURNING} FROM {schema}.cont_ejercicio ORDER BY ano ASC",
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al consultar los ejercicios")


# ------------------------------------------------------------------
# Obtener un ejercicio por id
# ------------------------------------------------------------------
def get_ejercicio(db, company_id: str, ejercicio_id: int):
    schema = _get_schema(db, company_id)
    try:
        row = fetch_one(
            db,
            f"SELECT {_RETURNING} FROM {schema}.cont_ejercicio WHERE id = %s",
            (ejercicio_id,),
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al consultar el ejercicio")

    if not row:
        _not_found(ejercicio_id)
    return row


# ------------------------------------------------------------------
# Crear ejercicio + generar los 12 meses de trabajo
# ------------------------------------------------------------------
def crear_ejercicio(db, company_id: str, data: EjercicioCreate):
    schema = _get_schema(db, company_id)

    # Verificar que no exista ya un ejercicio para ese año
    dup = fetch_one(
        db,
        f"SELECT id FROM {schema}.cont_ejercicio WHERE ano = %s",
        (data.ano,),
    )
    if dup:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un ejercicio contable para el año {data.ano}",
        )

    # Insertar ejercicio
    ejercicio = execute(
        db,
        f"""
        INSERT INTO {schema}.cont_ejercicio ({_COLS})
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING {_RETURNING}
        """,
        (data.ano, data.fecha_i, data.fecha_f, data.obser, data.status, data.bloqueo),
        returning=True,
    )

    # Generar los 12 meses de trabajo
    # Status='4' y Bloqueo='1' — el usuario los abre manualmente
    ano_int = int(data.ano)
    meses_cols = (
        "n_mes_contble, n_mes_sistema, mes, ano, status, bloqueo, "
        "ejercicio, tipo, fecha_i, fecha_f, fecha_creado"
    )
    meses_returning = (
        "id, n_mes_contble, n_mes_sistema, mes, ano, status, bloqueo, "
        "ejercicio, tipo, usuario, fecha_i, fecha_f, fecha_cierre, fecha_creado"
    )
    placeholders = ", ".join(["(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())"] * 12)
    params = []
    for n in range(1, 13):
        ultimo_dia = monthrange(ano_int, n)[1]
        fecha_i = date(ano_int, n, 1)
        fecha_f = date(ano_int, n, ultimo_dia)
        params.extend([
            n,                      # n_mes_contble
            n,                      # n_mes_sistema
            _NOMBRES_MESES[n - 1],  # mes
            data.ano,               # ano
            "4",                    # status — cerrado, el usuario abre manualmente
            "1",                    # bloqueo
            data.ano,               # ejercicio
            "N",                    # tipo
            fecha_i,                # fecha_i
            fecha_f,                # fecha_f
        ])

    meses = execute_all(
        db,
        f"""
        INSERT INTO {schema}.cont_meses_trab ({meses_cols})
        VALUES {placeholders}
        ON CONFLICT DO NOTHING
        RETURNING {meses_returning}
        """,
        params,
    )

    return {"ejercicio": ejercicio, "meses_creados": meses}


# ------------------------------------------------------------------
# Actualizar un ejercicio
# ------------------------------------------------------------------
def actualizar_ejercicio(db, company_id: str, ejercicio_id: int, data: EjercicioUpdate):
    get_ejercicio(db, company_id, ejercicio_id)

    campos = data.model_dump(exclude_unset=True)
    if not campos:
        return get_ejercicio(db, company_id, ejercicio_id)

    schema = _get_schema(db, company_id)
    columnas = ", ".join(f"{col} = %s" for col in campos.keys())
    valores = list(campos.values()) + [ejercicio_id]

    return execute(
        db,
        f"UPDATE {schema}.cont_ejercicio SET {columnas} WHERE id = %s RETURNING {_RETURNING}",
        valores,
        returning=True,
    )


# ------------------------------------------------------------------
# Eliminar un ejercicio
# ------------------------------------------------------------------
def eliminar_ejercicio(db, company_id: str, ejercicio_id: int):
    get_ejercicio(db, company_id, ejercicio_id)
    schema = _get_schema(db, company_id)
    execute(db, f"DELETE FROM {schema}.cont_ejercicio WHERE id = %s", (ejercicio_id,))
    return {"detail": f"Ejercicio con id={ejercicio_id} eliminado correctamente"}
