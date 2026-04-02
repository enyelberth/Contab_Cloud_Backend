"""
Funciones de habilidades de IA reutilizables para el ERP Multi-Sede.

Cada función encapsula una capacidad analítica específica que delega al
modelo Claude con pensamiento adaptativo (adaptive thinking). Las funciones
son asíncronas y reciben el cliente de Anthropic como dependencia para
facilitar el testing y la inyección de dependencias en FastAPI.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from app.ai.templates import (
    SYSTEM_ERP_ASSISTANT,
    SYSTEM_FINANCIAL_ANALYST,
    SYSTEM_INVENTORY_ANALYST,
    SYSTEM_REPORT_GENERATOR,
    SYSTEM_SALES_ANALYST,
)

logger = logging.getLogger(__name__)

# Modelo y parámetros por defecto para todas las habilidades
_MODEL = "claude-opus-4-5"
_MAX_TOKENS = 8192
_THINKING_CONFIG: dict[str, Any] = {"type": "enabled", "budget_tokens": 5000}


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _extract_json_from_text(text: str) -> dict:
    """
    Extrae y parsea un objeto JSON de una cadena de texto.

    Intenta los siguientes métodos en orden:
    1. Parseo directo del texto completo.
    2. Extracción del primer bloque de código Markdown ```json ... ```.
    3. Extracción del primer objeto JSON delimitado por ``{ ... }``.

    Args:
        text: Texto que contiene (o es) un objeto JSON.

    Returns:
        Diccionario Python con el contenido parseado.

    Raises:
        ValueError: Si no se puede extraer un JSON válido del texto.
    """
    # 1. Parseo directo
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 2. Bloque de código Markdown ```json ... ``` o ``` ... ```
    md_pattern = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", stripped, re.IGNORECASE)
    if md_pattern:
        try:
            return json.loads(md_pattern.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Primer objeto JSON { ... } en el texto
    brace_pattern = re.search(r"\{[\s\S]*\}", stripped)
    if brace_pattern:
        try:
            return json.loads(brace_pattern.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"No se pudo extraer un JSON válido del texto. "
        f"Primeros 200 caracteres: {text[:200]!r}"
    )


def _extract_text_from_response(response: anthropic.types.Message) -> str:
    """
    Extrae el texto del primer bloque TextBlock de una respuesta de Anthropic.

    Args:
        response: Objeto Message devuelto por la API de Anthropic.

    Returns:
        Texto combinado de todos los bloques de texto en la respuesta.
    """
    parts: list[str] = []
    for block in response.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts).strip()


def _build_usage_dict(response: anthropic.types.Message) -> dict:
    """
    Construye un diccionario de uso de tokens desde el objeto Usage de Anthropic.

    Args:
        response: Objeto Message con atributo usage.

    Returns:
        Diccionario con input_tokens, output_tokens y cache_read_input_tokens.
    """
    usage = response.usage
    result = {
        "input_tokens": getattr(usage, "input_tokens", 0),
        "output_tokens": getattr(usage, "output_tokens", 0),
    }
    cache_read = getattr(usage, "cache_read_input_tokens", None)
    if cache_read is not None:
        result["cache_read_input_tokens"] = cache_read
    return result


# ---------------------------------------------------------------------------
# Habilidades principales
# ---------------------------------------------------------------------------


async def analyze_sales(
    client: anthropic.Anthropic,
    data: dict,
    question: str,
    branch_context: str = "",
) -> dict:
    """
    Analiza datos de ventas y genera insights, tendencias y recomendaciones.

    Utiliza el template SYSTEM_SALES_ANALYST con pensamiento adaptativo para
    procesar los datos de ventas proporcionados y responder a la pregunta
    específica del usuario.

    Args:
        client: Cliente instanciado de Anthropic SDK.
        data: Datos de ventas en formato dict (ventas, ítems, clientes, pagos).
        question: Pregunta o área de análisis específica solicitada.
        branch_context: Descripción opcional de la sucursal o contexto adicional.

    Returns:
        Diccionario con las claves:
            - analysis (str): Análisis detallado del modelo.
            - insights (list[str]): Hallazgos e insights clave.
            - recommendations (list[str]): Acciones recomendadas priorizadas.
            - model (str): Identificador del modelo utilizado.
            - usage (dict): Estadísticas de uso de tokens.

    Raises:
        anthropic.APIError: Si la API de Anthropic devuelve un error.
        ValueError: Si la respuesta no puede ser parseada como JSON.
    """
    context_note = f"\n\n**Contexto de sucursal:** {branch_context}" if branch_context else ""

    user_message = (
        f"**Datos de ventas para análisis:**\n\n"
        f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
        f"{context_note}\n\n"
        f"**Pregunta/Análisis solicitado:** {question}\n\n"
        f"Responde en formato JSON con esta estructura exacta:\n"
        f'{{"analysis": "texto del análisis", '
        f'"insights": ["insight 1", "insight 2"], '
        f'"recommendations": ["recomendación 1", "recomendación 2"]}}'
    )

    logger.info("Iniciando análisis de ventas. Pregunta: %s", question[:80])

    response = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        thinking=_THINKING_CONFIG,
        system=SYSTEM_SALES_ANALYST,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = _extract_text_from_response(response)

    try:
        parsed = _extract_json_from_text(raw_text)
    except ValueError:
        logger.warning("No se pudo parsear JSON de análisis de ventas. Usando texto raw.")
        parsed = {}

    return {
        "analysis": parsed.get("analysis", raw_text),
        "insights": parsed.get("insights", []),
        "recommendations": parsed.get("recommendations", []),
        "model": response.model,
        "usage": _build_usage_dict(response),
    }


async def analyze_inventory(
    client: anthropic.Anthropic,
    data: dict,
    question: str,
    branch_context: str = "",
) -> dict:
    """
    Analiza el estado del inventario, identifica alertas y sugiere acciones de reabastecimiento.

    Usa el template SYSTEM_INVENTORY_ANALYST para detectar stock bajo, productos
    sin movimiento, puntos de reorden y anomalías en el inventario.

    Args:
        client: Cliente instanciado de Anthropic SDK.
        data: Datos de inventario (stock por producto/sucursal, movimientos, proveedores).
        question: Pregunta o área de análisis específica sobre el inventario.
        branch_context: Descripción opcional de la sucursal o contexto adicional.

    Returns:
        Diccionario con las claves:
            - analysis (str): Análisis detallado del estado del inventario.
            - alerts (list[str]): Alertas críticas que requieren atención inmediata.
            - recommendations (list[str]): Acciones de reabastecimiento y optimización.
            - model (str): Identificador del modelo utilizado.
            - usage (dict): Estadísticas de uso de tokens.

    Raises:
        anthropic.APIError: Si la API de Anthropic devuelve un error.
        ValueError: Si la respuesta no puede ser parseada como JSON.
    """
    context_note = f"\n\n**Contexto de sucursal:** {branch_context}" if branch_context else ""

    user_message = (
        f"**Datos de inventario para análisis:**\n\n"
        f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
        f"{context_note}\n\n"
        f"**Pregunta/Análisis solicitado:** {question}\n\n"
        f"Responde en formato JSON con esta estructura exacta:\n"
        f'{{"analysis": "texto del análisis", '
        f'"alerts": ["alerta crítica 1", "alerta crítica 2"], '
        f'"recommendations": ["recomendación 1", "recomendación 2"]}}'
    )

    logger.info("Iniciando análisis de inventario. Pregunta: %s", question[:80])

    response = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        thinking=_THINKING_CONFIG,
        system=SYSTEM_INVENTORY_ANALYST,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = _extract_text_from_response(response)

    try:
        parsed = _extract_json_from_text(raw_text)
    except ValueError:
        logger.warning("No se pudo parsear JSON de análisis de inventario. Usando texto raw.")
        parsed = {}

    return {
        "analysis": parsed.get("analysis", raw_text),
        "alerts": parsed.get("alerts", []),
        "recommendations": parsed.get("recommendations", []),
        "model": response.model,
        "usage": _build_usage_dict(response),
    }


async def analyze_financial(
    client: anthropic.Anthropic,
    data: dict,
    question: str,
    period: str = "",
) -> dict:
    """
    Analiza datos financieros del ERP: flujo de caja, márgenes y rentabilidad.

    Usa el template SYSTEM_FINANCIAL_ANALYST con pensamiento adaptativo para
    procesar datos financieros consolidados y responder preguntas sobre la
    salud económica del negocio.

    Args:
        client: Cliente instanciado de Anthropic SDK.
        data: Datos financieros (ventas, compras, pagos, cajas, tipos de cambio).
        question: Pregunta o área de análisis financiero específica.
        period: Descripción del período analizado (ej. "Q1 2025", "Enero 2025").

    Returns:
        Diccionario con las claves:
            - analysis (str): Análisis financiero detallado.
            - insights (list[str]): Hallazgos financieros clave.
            - recommendations (list[str]): Acciones financieras recomendadas.
            - model (str): Identificador del modelo utilizado.
            - usage (dict): Estadísticas de uso de tokens.

    Raises:
        anthropic.APIError: Si la API de Anthropic devuelve un error.
        ValueError: Si la respuesta no puede ser parseada como JSON.
    """
    period_note = f"\n\n**Período de análisis:** {period}" if period else ""

    user_message = (
        f"**Datos financieros para análisis:**\n\n"
        f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
        f"{period_note}\n\n"
        f"**Pregunta/Análisis solicitado:** {question}\n\n"
        f"Responde en formato JSON con esta estructura exacta:\n"
        f'{{"analysis": "texto del análisis financiero", '
        f'"insights": ["insight financiero 1", "insight financiero 2"], '
        f'"recommendations": ["recomendación financiera 1", "recomendación financiera 2"]}}'
    )

    logger.info("Iniciando análisis financiero. Período: %s | Pregunta: %s", period, question[:60])

    response = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        thinking=_THINKING_CONFIG,
        system=SYSTEM_FINANCIAL_ANALYST,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = _extract_text_from_response(response)

    try:
        parsed = _extract_json_from_text(raw_text)
    except ValueError:
        logger.warning("No se pudo parsear JSON de análisis financiero. Usando texto raw.")
        parsed = {}

    return {
        "analysis": parsed.get("analysis", raw_text),
        "insights": parsed.get("insights", []),
        "recommendations": parsed.get("recommendations", []),
        "model": response.model,
        "usage": _build_usage_dict(response),
    }


async def generate_report(
    client: anthropic.Anthropic,
    report_type: str,
    data: dict,
    format_instructions: str = "",
) -> dict:
    """
    Genera un reporte empresarial estructurado basado en datos del ERP.

    Usa el template SYSTEM_REPORT_GENERATOR para crear reportes profesionales
    con título, secciones estructuradas, KPIs y recomendaciones accionables.

    Args:
        client: Cliente instanciado de Anthropic SDK.
        report_type: Tipo de reporte (ventas, inventario, financiero, ejecutivo, etc.).
        data: Datos del ERP necesarios para generar el reporte.
        format_instructions: Instrucciones adicionales de formato o contenido.

    Returns:
        Diccionario con las claves:
            - title (str): Título del reporte generado.
            - content (str): Contenido completo del reporte en texto/markdown.
            - sections (list[dict]): Lista de secciones con 'title' y 'content'.
            - model (str): Identificador del modelo utilizado.
            - usage (dict): Estadísticas de uso de tokens.

    Raises:
        anthropic.APIError: Si la API de Anthropic devuelve un error.
        ValueError: Si la respuesta no puede ser parseada como JSON.
    """
    format_note = (
        f"\n\n**Instrucciones de formato adicionales:** {format_instructions}"
        if format_instructions
        else ""
    )

    user_message = (
        f"**Tipo de reporte solicitado:** {report_type.upper()}\n\n"
        f"**Datos del ERP para el reporte:**\n\n"
        f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
        f"{format_note}\n\n"
        f"Genera el reporte completo y responde en formato JSON con esta estructura exacta:\n"
        f'{{"title": "Título del Reporte", '
        f'"content": "Contenido completo del reporte en markdown", '
        f'"sections": [{{"title": "Sección 1", "content": "Contenido de la sección 1"}}, '
        f'{{"title": "Sección 2", "content": "Contenido de la sección 2"}}]}}'
    )

    logger.info("Generando reporte tipo: %s", report_type)

    response = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        thinking=_THINKING_CONFIG,
        system=SYSTEM_REPORT_GENERATOR,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = _extract_text_from_response(response)

    try:
        parsed = _extract_json_from_text(raw_text)
    except ValueError:
        logger.warning("No se pudo parsear JSON del reporte. Usando texto raw como contenido.")
        parsed = {}

    return {
        "title": parsed.get("title", f"Reporte de {report_type.capitalize()}"),
        "content": parsed.get("content", raw_text),
        "sections": parsed.get("sections", []),
        "model": response.model,
        "usage": _build_usage_dict(response),
    }


async def erp_chat(
    client: anthropic.Anthropic,
    messages: list[dict],
    context: dict | None = None,
) -> str:
    """
    Ejecuta una conversación multi-turno con el asistente ERP de propósito general.

    Usa el template SYSTEM_ERP_ASSISTANT para responder preguntas generales
    sobre el ERP, sus módulos, datos y procesos de negocio.

    Args:
        client: Cliente instanciado de Anthropic SDK.
        messages: Lista de mensajes en formato [{"role": "user"|"assistant", "content": "..."}].
                  El historial completo de la conversación en orden cronológico.
        context: Diccionario opcional con datos de contexto del ERP (sucursal activa,
                 período, datos del usuario, etc.) que se inyecta en el sistema prompt.

    Returns:
        Texto de la respuesta del asistente.

    Raises:
        anthropic.APIError: Si la API de Anthropic devuelve un error.
        ValueError: Si la lista de mensajes está vacía o tiene formato inválido.
    """
    if not messages:
        raise ValueError("La lista de mensajes no puede estar vacía.")

    # Construir el system prompt con contexto adicional si se proporciona
    system_prompt = SYSTEM_ERP_ASSISTANT
    if context:
        context_json = json.dumps(context, ensure_ascii=False, indent=2)
        system_prompt = (
            f"{SYSTEM_ERP_ASSISTANT}\n\n"
            f"## Contexto Actual del Usuario\n"
            f"```json\n{context_json}\n```"
        )

    # Validar y normalizar la lista de mensajes para la API de Anthropic
    api_messages: list[dict] = []
    for msg in messages:
        role = msg.get("role", "").lower()
        content = msg.get("content", "")
        if role not in ("user", "assistant"):
            logger.warning("Rol de mensaje inválido ignorado: %r", role)
            continue
        if not content:
            logger.warning("Mensaje con contenido vacío ignorado (role=%s).", role)
            continue
        api_messages.append({"role": role, "content": content})

    if not api_messages:
        raise ValueError("No hay mensajes válidos para enviar a la API.")

    # El primer mensaje debe ser del usuario según la API de Anthropic
    if api_messages[0]["role"] != "user":
        raise ValueError("El primer mensaje de la conversación debe tener role='user'.")

    logger.info(
        "Iniciando chat ERP. Turnos en historial: %d | Contexto: %s",
        len(api_messages),
        "sí" if context else "no",
    )

    response = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        thinking=_THINKING_CONFIG,
        system=system_prompt,
        messages=api_messages,
    )

    return _extract_text_from_response(response)
