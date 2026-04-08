from fastapi import HTTPException

from app.database import execute, execute_all, fetch_all, fetch_one
from app.comprobantes.schemas import (
    MaestroComprobanteCreate,
    MaestroComprobanteUpdate,
    DetalleComprobanteCreate,
    DetalleComprobanteUpdate,
)

_MAESTRO_COLS = (
    "fecha_comprobante, tipo, txt_descripcion, txt_status, txt_id_usuario, "
    "txt_id_pc, txt_modo_creacion, txt_comentario, clase, num_comp, "
    "num_transferencia, sg_moneda, n_tipo, n_sub_tipo, num_operacion_comp"
)

_MAESTRO_RETURNING = (
    "num_comprobante, fecha_comprobante, tipo, txt_descripcion, txt_status, "
    "txt_id_usuario, fecha_hora_creacion, txt_id_pc, txt_modo_creacion, "
    "txt_comentario, clase, num_comp, num_transferencia, sg_moneda, "
    "n_tipo, n_sub_tipo, num_operacion_comp, usuario_anulo, fecha_hora_anulo, "
    "usuario_modifico, fecha_hora_modifico"
)

_DETALLE_COLS = (
    "num_comprobante, num_item, txt_cuenta, nom_corto, txt_tipo, "
    "txt_referencia, txt_concepto, num_debito, num_credito, fecha, "
    "auxiliar, tipo_auxiliar"
)

_DETALLE_RETURNING = (
    "id, num_comprobante, num_item, txt_cuenta, nom_corto, txt_tipo, "
    "txt_referencia, txt_concepto, num_debito, num_credito, fecha, "
    "auxiliar, tipo_auxiliar"
)


def _get_schema(db, company_id: str) -> str:
    row = fetch_one(
        db,
        "SELECT schema_name FROM global.tenants WHERE uuid = %s::uuid AND deleted_at IS NULL",
        (company_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return row["schema_name"]


def _maestro_not_found(num: int):
    raise HTTPException(status_code=404, detail=f"Comprobante num={num} no encontrado")


def _detalle_not_found(detalle_id: int):
    raise HTTPException(status_code=404, detail=f"Detalle id={detalle_id} no encontrado")


# ──────────────────────────────────────────────────────────────
# Maestro — CRUD
# ──────────────────────────────────────────────────────────────

def get_comprobantes(db, company_id: str):
    schema = _get_schema(db, company_id)
    try:
        return fetch_all(
            db,
            f"SELECT {_MAESTRO_RETURNING} FROM {schema}.cont_maestro_comprobante "
            f"ORDER BY num_comprobante DESC",
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al consultar los comprobantes")


def get_comprobante(db, company_id: str, num_comprobante: int):
    schema = _get_schema(db, company_id)
    try:
        row = fetch_one(
            db,
            f"SELECT {_MAESTRO_RETURNING} FROM {schema}.cont_maestro_comprobante "
            f"WHERE num_comprobante = %s",
            (num_comprobante,),
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al consultar el comprobante")
    if not row:
        _maestro_not_found(num_comprobante)
    return row


def get_comprobante_con_detalles(db, company_id: str, num_comprobante: int):
    maestro = get_comprobante(db, company_id, num_comprobante)
    detalles = get_detalles(db, company_id, num_comprobante)
    return {**maestro, "detalles": detalles}


def crear_comprobante(db, company_id: str, data: MaestroComprobanteCreate):
    schema = _get_schema(db, company_id)

    maestro = execute(
        db,
        f"""
        INSERT INTO {schema}.cont_maestro_comprobante ({_MAESTRO_COLS})
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING {_MAESTRO_RETURNING}
        """,
        (
            data.fecha_comprobante,
            data.tipo,
            data.txt_descripcion,
            data.txt_status,
            data.txt_id_usuario,
            data.txt_id_pc,
            data.txt_modo_creacion,
            data.txt_comentario,
            data.clase,
            data.num_comp,
            data.num_transferencia,
            data.sg_moneda,
            data.n_tipo,
            data.n_sub_tipo,
            data.num_operacion_comp,
        ),
        returning=True,
    )

    detalles_creados = []
    if data.detalles:
        num = maestro["num_comprobante"]
        detalles_creados = _insertar_detalles(db, schema, num, data.detalles)

    return {"comprobante": maestro, "detalles": detalles_creados}


def actualizar_comprobante(db, company_id: str, num_comprobante: int, data: MaestroComprobanteUpdate):
    get_comprobante(db, company_id, num_comprobante)

    campos = data.model_dump(exclude_unset=True)
    if not campos:
        return get_comprobante(db, company_id, num_comprobante)

    schema = _get_schema(db, company_id)
    columnas = ", ".join(f"{col} = %s" for col in campos.keys())
    valores = list(campos.values()) + [num_comprobante]

    return execute(
        db,
        f"UPDATE {schema}.cont_maestro_comprobante SET {columnas} "
        f"WHERE num_comprobante = %s RETURNING {_MAESTRO_RETURNING}",
        valores,
        returning=True,
    )


def eliminar_comprobante(db, company_id: str, num_comprobante: int):
    get_comprobante(db, company_id, num_comprobante)
    schema = _get_schema(db, company_id)
    execute(
        db,
        f"DELETE FROM {schema}.cont_detalle_comprobante WHERE num_comprobante = %s",
        (num_comprobante,),
    )
    execute(
        db,
        f"DELETE FROM {schema}.cont_maestro_comprobante WHERE num_comprobante = %s",
        (num_comprobante,),
    )
    return {"detail": f"Comprobante num={num_comprobante} eliminado correctamente"}


# ──────────────────────────────────────────────────────────────
# Detalle — helpers
# ──────────────────────────────────────────────────────────────

def _insertar_detalles(db, schema: str, num_comprobante: int, detalles: list):
    if not detalles:
        return []
    placeholders = ", ".join(["(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"] * len(detalles))
    params = []
    for d in detalles:
        params.extend([
            num_comprobante,
            d.num_item,
            d.txt_cuenta,
            d.nom_corto,
            d.txt_tipo,
            d.txt_referencia,
            d.txt_concepto,
            d.num_debito,
            d.num_credito,
            d.fecha,
            d.auxiliar,
            d.tipo_auxiliar,
        ])
    return execute_all(
        db,
        f"INSERT INTO {schema}.cont_detalle_comprobante ({_DETALLE_COLS}) "
        f"VALUES {placeholders} RETURNING {_DETALLE_RETURNING}",
        params,
    )


# ──────────────────────────────────────────────────────────────
# Detalle — CRUD
# ──────────────────────────────────────────────────────────────

def get_detalles(db, company_id: str, num_comprobante: int):
    schema = _get_schema(db, company_id)
    try:
        return fetch_all(
            db,
            f"SELECT {_DETALLE_RETURNING} FROM {schema}.cont_detalle_comprobante "
            f"WHERE num_comprobante = %s ORDER BY num_item ASC, id ASC",
            (num_comprobante,),
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al consultar los detalles")


def get_detalle(db, company_id: str, num_comprobante: int, detalle_id: int):
    schema = _get_schema(db, company_id)
    try:
        row = fetch_one(
            db,
            f"SELECT {_DETALLE_RETURNING} FROM {schema}.cont_detalle_comprobante "
            f"WHERE id = %s AND num_comprobante = %s",
            (detalle_id, num_comprobante),
        )
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al consultar el detalle")
    if not row:
        _detalle_not_found(detalle_id)
    return row


def agregar_detalle(db, company_id: str, num_comprobante: int, data: DetalleComprobanteCreate):
    get_comprobante(db, company_id, num_comprobante)
    schema = _get_schema(db, company_id)
    return execute(
        db,
        f"""
        INSERT INTO {schema}.cont_detalle_comprobante ({_DETALLE_COLS})
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING {_DETALLE_RETURNING}
        """,
        (
            num_comprobante,
            data.num_item,
            data.txt_cuenta,
            data.nom_corto,
            data.txt_tipo,
            data.txt_referencia,
            data.txt_concepto,
            data.num_debito,
            data.num_credito,
            data.fecha,
            data.auxiliar,
            data.tipo_auxiliar,
        ),
        returning=True,
    )


def actualizar_detalle(db, company_id: str, num_comprobante: int, detalle_id: int, data: DetalleComprobanteUpdate):
    get_detalle(db, company_id, num_comprobante, detalle_id)

    campos = data.model_dump(exclude_unset=True)
    if not campos:
        return get_detalle(db, company_id, num_comprobante, detalle_id)

    schema = _get_schema(db, company_id)
    columnas = ", ".join(f"{col} = %s" for col in campos.keys())
    valores = list(campos.values()) + [detalle_id, num_comprobante]

    return execute(
        db,
        f"UPDATE {schema}.cont_detalle_comprobante SET {columnas} "
        f"WHERE id = %s AND num_comprobante = %s RETURNING {_DETALLE_RETURNING}",
        valores,
        returning=True,
    )


def eliminar_detalle(db, company_id: str, num_comprobante: int, detalle_id: int):
    get_detalle(db, company_id, num_comprobante, detalle_id)
    schema = _get_schema(db, company_id)
    execute(
        db,
        f"DELETE FROM {schema}.cont_detalle_comprobante WHERE id = %s AND num_comprobante = %s",
        (detalle_id, num_comprobante),
    )
    return {"detail": f"Detalle id={detalle_id} eliminado correctamente"}
