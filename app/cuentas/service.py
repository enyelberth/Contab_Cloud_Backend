from typing import List

from fastapi import HTTPException

from app.database import execute, execute_all, fetch_all, fetch_one
from app.cuentas.schemas import CuentaCreate, CuentaUpdate

# Columnas reutilizadas en todos los queries
_COLS = (
    "txt_cuenta, txt_denominacion, txt_nom_corto, num_nivel, txt_status, "
    "txt_comentario, cuenta_padre, nomb_cuenta_padre, "
    "num_tipo_aux, tipo_aux, num_tipo_cuenta, cod_tipo_aux, num_aux"
)
_RETURNING = (
    "id, txt_cuenta, txt_denominacion, txt_nom_corto, num_nivel, txt_status, "
    "txt_comentario, cuenta_padre, nomb_cuenta_padre, "
    "num_tipo_aux, tipo_aux, num_tipo_cuenta, cod_tipo_aux, num_aux"
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


def _cuenta_params(c: CuentaCreate) -> tuple:
    return (
        c.txt_cuenta, c.txt_denominacion, c.txt_nom_corto,
        c.num_nivel, c.txt_status, c.txt_comentario,
        c.cuenta_padre, c.nomb_cuenta_padre,
        c.num_tipo_aux, c.tipo_aux, c.num_tipo_cuenta,
        c.cod_tipo_aux, c.num_aux,
    )


def _not_found(company_id: str, txt_cuenta: str):
    raise HTTPException(
        status_code=404,
        detail=f"Cuenta '{txt_cuenta}' no encontrada en empresa {company_id}",
    )


# ------------------------------------------------------------------
# Listar todas las cuentas de una empresa
# ------------------------------------------------------------------
def get_cuentas(db, company_id: str):
    schema = _get_schema(db, company_id)
    try:
        return fetch_all(
            db,
            f"SELECT {_RETURNING} FROM {schema}.cont_cuentas ORDER BY txt_cuenta ASC",
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al consultar el plan de cuentas")


# ------------------------------------------------------------------
# Obtener una cuenta por su código
# ------------------------------------------------------------------
def get_cuenta(db, company_id: str, txt_cuenta: str):
    schema = _get_schema(db, company_id)
    try:
        row = fetch_one(
            db,
            f"SELECT {_RETURNING} FROM {schema}.cont_cuentas WHERE txt_cuenta = %s",
            (txt_cuenta,),
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al consultar la cuenta")

    if not row:
        _not_found(company_id, txt_cuenta)
    return row


# ------------------------------------------------------------------
# Crear una sola cuenta
# ------------------------------------------------------------------
def crear_cuenta(db, company_id: str, data: CuentaCreate):
    schema = _get_schema(db, company_id)
    try:
        return execute(
            db,
            f"INSERT INTO {schema}.cont_cuentas ({_COLS}) VALUES {_ROW_PH} RETURNING {_RETURNING}",
            _cuenta_params(data),
            returning=True,
        )
    except Exception as e:
        db.rollback()
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe una cuenta con el código '{data.txt_cuenta}'",
            )
        raise HTTPException(status_code=500, detail="Error al crear la cuenta")


# ------------------------------------------------------------------
# Actualizar una cuenta (solo los campos enviados)
# ------------------------------------------------------------------
def actualizar_cuenta(db, company_id: str, txt_cuenta: str, data: CuentaUpdate):
    get_cuenta(db, company_id, txt_cuenta)

    campos = data.model_dump(exclude_unset=True)
    if not campos:
        return get_cuenta(db, company_id, txt_cuenta)

    schema = _get_schema(db, company_id)
    columnas = ", ".join(f"{col} = %s" for col in campos.keys())
    valores = list(campos.values()) + [txt_cuenta]

    return execute(
        db,
        f"UPDATE {schema}.cont_cuentas SET {columnas} WHERE txt_cuenta = %s RETURNING {_RETURNING}",
        valores,
        returning=True,
    )


# ------------------------------------------------------------------
# Eliminar una cuenta
# ------------------------------------------------------------------
def eliminar_cuenta(db, company_id: str, txt_cuenta: str):
    get_cuenta(db, company_id, txt_cuenta)
    schema = _get_schema(db, company_id)
    execute(db, f"DELETE FROM {schema}.cont_cuentas WHERE txt_cuenta = %s", (txt_cuenta,))
    return {"detail": f"Cuenta '{txt_cuenta}' eliminada correctamente"}


# ------------------------------------------------------------------
# Crear múltiples cuentas en una sola llamada (lote)
# ------------------------------------------------------------------
def crear_cuentas_lote(db, company_id: str, cuentas: List[CuentaCreate]):
    if not cuentas:
        return {"insertadas": 0, "omitidas": 0, "cuentas": []}

    schema = _get_schema(db, company_id)
    placeholders = ", ".join([_ROW_PH] * len(cuentas))
    params = []
    for c in cuentas:
        params.extend(_cuenta_params(c))

    try:
        filas = execute_all(
            db,
            f"""
            INSERT INTO {schema}.cont_cuentas ({_COLS})
            VALUES {placeholders}
            ON CONFLICT (txt_cuenta) DO NOTHING
            RETURNING {_RETURNING}
            """,
            params,
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al insertar el lote de cuentas")

    return {
        "insertadas": len(filas),
        "omitidas": len(cuentas) - len(filas),
        "cuentas": filas,
    }


# ------------------------------------------------------------------
# Comparar el plan de cuentas entre 2 empresas
# ------------------------------------------------------------------
def comparar_cuentas(db, company_id_origen: str, company_id_destino: str):
    origen = get_cuentas(db, company_id_origen)
    destino = get_cuentas(db, company_id_destino)

    idx_origen = {r["txt_cuenta"]: r for r in origen}
    idx_destino = {r["txt_cuenta"]: r for r in destino}

    codigos_origen = set(idx_origen)
    codigos_destino = set(idx_destino)

    solo_en_origen = sorted(
        [idx_origen[c] for c in codigos_origen - codigos_destino],
        key=lambda r: r["txt_cuenta"],
    )
    solo_en_destino = sorted(
        [idx_destino[c] for c in codigos_destino - codigos_origen],
        key=lambda r: r["txt_cuenta"],
    )
    en_ambas = sorted(
        [idx_origen[c] for c in codigos_origen & codigos_destino],
        key=lambda r: r["txt_cuenta"],
    )

    return {
        "empresa_origen": company_id_origen,
        "empresa_destino": company_id_destino,
        "resumen": {
            "total_origen": len(origen),
            "total_destino": len(destino),
            "solo_en_origen": len(solo_en_origen),
            "solo_en_destino": len(solo_en_destino),
            "en_ambas": len(en_ambas),
        },
        "solo_en_origen": solo_en_origen,
        "solo_en_destino": solo_en_destino,
        "en_ambas": en_ambas,
    }


# ------------------------------------------------------------------
# Importar el plan de cuentas completo de una empresa a otra
# ------------------------------------------------------------------
def importar_cuentas(db, company_id_origen: str, company_id_destino: str, modo: str):
    if modo not in ("omitir", "reemplazar"):
        raise HTTPException(status_code=400, detail="modo debe ser 'omitir' o 'reemplazar'")

    schema_origen = _get_schema(db, company_id_origen)
    schema_destino = _get_schema(db, company_id_destino)

    if modo == "reemplazar":
        conflict_clause = f"""
            ON CONFLICT (txt_cuenta) DO UPDATE SET
                txt_denominacion  = EXCLUDED.txt_denominacion,
                txt_nom_corto     = EXCLUDED.txt_nom_corto,
                num_nivel         = EXCLUDED.num_nivel,
                txt_status        = EXCLUDED.txt_status,
                txt_comentario    = EXCLUDED.txt_comentario,
                cuenta_padre      = EXCLUDED.cuenta_padre,
                nomb_cuenta_padre = EXCLUDED.nomb_cuenta_padre,
                num_tipo_aux      = EXCLUDED.num_tipo_aux,
                tipo_aux          = EXCLUDED.tipo_aux,
                num_tipo_cuenta   = EXCLUDED.num_tipo_cuenta,
                cod_tipo_aux      = EXCLUDED.cod_tipo_aux,
                num_aux           = EXCLUDED.num_aux
        """
    else:
        conflict_clause = "ON CONFLICT (txt_cuenta) DO NOTHING"

    try:
        filas = execute_all(
            db,
            f"""
            INSERT INTO {schema_destino}.cont_cuentas ({_COLS})
            SELECT {_COLS} FROM {schema_origen}.cont_cuentas
            {conflict_clause}
            RETURNING {_RETURNING}
            """,
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al importar las cuentas")

    return {
        "empresa_origen": company_id_origen,
        "empresa_destino": company_id_destino,
        "modo": modo,
        "importadas": len(filas),
        "cuentas": filas,
    }
