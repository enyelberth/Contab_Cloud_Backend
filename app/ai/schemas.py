"""
Esquemas Pydantic v2 para las solicitudes y respuestas del módulo de IA.

Define los contratos de entrada y salida para todos los endpoints de IA,
garantizando validación de datos y documentación automática en FastAPI.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Mensajes y chat general
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    """Representa un único mensaje en una conversación multi-turno."""

    role: str = Field(
        ...,
        description="Rol del emisor del mensaje. Valores válidos: 'user' o 'assistant'.",
        examples=["user", "assistant"],
    )
    content: str = Field(
        ...,
        description="Contenido textual del mensaje.",
        examples=["¿Cuáles fueron las ventas del mes pasado?"],
    )


class ChatRequest(BaseModel):
    """Solicitud de chat con el asistente ERP de propósito general."""

    messages: list[ChatMessage] = Field(
        ...,
        description="Historial de mensajes de la conversación (orden cronológico).",
        min_length=1,
    )
    context: dict | None = Field(
        default=None,
        description=(
            "Datos de contexto adicionales del ERP (ej. sucursal activa, "
            "período seleccionado, datos del usuario) en formato JSON."
        ),
    )
    stream: bool = Field(
        default=False,
        description="Activa el streaming de la respuesta (no implementado aún, reservado).",
    )


class ChatResponse(BaseModel):
    """Respuesta del asistente ERP de propósito general."""

    response: str = Field(..., description="Texto de respuesta generado por el modelo.")
    model: str = Field(..., description="Identificador del modelo de IA utilizado.")
    usage: dict = Field(
        ...,
        description=(
            "Estadísticas de uso de tokens: input_tokens, output_tokens "
            "y opcionalmente cache_read_input_tokens."
        ),
    )


# ---------------------------------------------------------------------------
# Análisis de ventas
# ---------------------------------------------------------------------------


class SalesAnalysisRequest(BaseModel):
    """Solicitud de análisis inteligente de datos de ventas."""

    branch_id: int | None = Field(
        default=None,
        description="ID de la sucursal a analizar. Si es None, se analiza toda la empresa.",
        gt=0,
    )
    date_from: str | None = Field(
        default=None,
        description="Fecha de inicio del período de análisis (formato ISO 8601: YYYY-MM-DD).",
        examples=["2025-01-01"],
    )
    date_to: str | None = Field(
        default=None,
        description="Fecha de fin del período de análisis (formato ISO 8601: YYYY-MM-DD).",
        examples=["2025-12-31"],
    )
    question: str = Field(
        ...,
        description="Pregunta o área de análisis específica solicitada por el usuario.",
        min_length=5,
        examples=["¿Cuáles son los productos con mayor margen de ganancia este mes?"],
    )
    data: dict = Field(
        ...,
        description=(
            "Datos de ventas en formato JSON (ventas, ítems, clientes, "
            "métodos de pago, etc.) extraídos previamente del ERP."
        ),
    )


# ---------------------------------------------------------------------------
# Análisis de inventario
# ---------------------------------------------------------------------------


class InventoryAnalysisRequest(BaseModel):
    """Solicitud de análisis inteligente del estado del inventario."""

    branch_id: int | None = Field(
        default=None,
        description="ID de la sucursal a analizar. Si es None, se analiza el inventario global.",
        gt=0,
    )
    question: str = Field(
        ...,
        description="Pregunta o área de análisis específica sobre el inventario.",
        min_length=5,
        examples=["¿Qué productos necesitan reabastecimiento urgente?"],
    )
    data: dict = Field(
        ...,
        description=(
            "Datos de inventario en formato JSON (stock por producto/sucursal, "
            "movimientos, puntos de reorden, etc.) extraídos del ERP."
        ),
    )


# ---------------------------------------------------------------------------
# Análisis financiero
# ---------------------------------------------------------------------------


class FinancialAnalysisRequest(BaseModel):
    """Solicitud de análisis financiero del ERP."""

    branch_id: int | None = Field(
        default=None,
        description="ID de la sucursal a analizar. Si es None, se analiza la empresa completa.",
        gt=0,
    )
    period: str = Field(
        ...,
        description=(
            "Descripción del período de análisis "
            "(ej. 'Q1 2025', 'Enero-Marzo 2025', '2025-01 al 2025-03')."
        ),
        min_length=3,
        examples=["Q1 2025", "Enero 2025", "2025-01-01 al 2025-03-31"],
    )
    question: str = Field(
        ...,
        description="Pregunta o área de análisis financiero específica.",
        min_length=5,
        examples=["¿Cuál es el flujo de caja neto y la rentabilidad del trimestre?"],
    )
    data: dict = Field(
        ...,
        description=(
            "Datos financieros en formato JSON (ventas, compras, pagos, "
            "saldos de caja, tasas de cambio, etc.) extraídos del ERP."
        ),
    )


# ---------------------------------------------------------------------------
# Generación de reportes
# ---------------------------------------------------------------------------


class ReportRequest(BaseModel):
    """Solicitud de generación de un reporte empresarial estructurado."""

    report_type: str = Field(
        ...,
        description=(
            "Tipo de reporte a generar. Valores sugeridos: 'ventas', 'inventario', "
            "'financiero', 'compras', 'clientes', 'ejecutivo', 'auditoria'."
        ),
        min_length=3,
        examples=["ventas", "inventario", "financiero", "ejecutivo"],
    )
    branch_id: int | None = Field(
        default=None,
        description="ID de la sucursal para el reporte. None genera reporte consolidado.",
        gt=0,
    )
    data: dict = Field(
        ...,
        description="Datos estructurados del ERP necesarios para generar el reporte.",
    )
    format_instructions: str | None = Field(
        default=None,
        description=(
            "Instrucciones adicionales de formato o contenido para personalizar el reporte "
            "(ej. 'incluir gráficas descriptivas', 'formato ejecutivo de una página')."
        ),
    )


# ---------------------------------------------------------------------------
# Tareas de agentes
# ---------------------------------------------------------------------------


class AgentTaskRequest(BaseModel):
    """Solicitud de ejecución de una tarea por un agente de IA del ERP."""

    task: str = Field(
        ...,
        description="Descripción detallada de la tarea que debe ejecutar el agente.",
        min_length=10,
        examples=[
            "Analiza el inventario crítico de todas las sucursales y genera "
            "un plan de reabastecimiento para los próximos 30 días."
        ],
    )
    context: dict | None = Field(
        default=None,
        description=(
            "Contexto adicional para el agente: datos del ERP, parámetros de negocio, "
            "restricciones o preferencias del usuario."
        ),
    )
    max_turns: int = Field(
        default=10,
        description="Número máximo de iteraciones (turnos) que puede realizar el agente.",
        ge=1,
        le=50,
    )


# ---------------------------------------------------------------------------
# Respuestas de análisis y reportes
# ---------------------------------------------------------------------------


class AnalysisResponse(BaseModel):
    """Respuesta estructurada de un análisis de IA (ventas, inventario, finanzas)."""

    analysis: str = Field(
        ...,
        description="Análisis detallado en texto libre con el razonamiento del modelo.",
    )
    insights: list[str] = Field(
        ...,
        description="Lista de hallazgos e insights clave identificados en los datos.",
    )
    recommendations: list[str] = Field(
        ...,
        description="Lista de recomendaciones accionables ordenadas por prioridad.",
    )
    model: str = Field(..., description="Identificador del modelo de IA utilizado.")


class ReportResponse(BaseModel):
    """Respuesta estructurada con el reporte generado por la IA."""

    title: str = Field(..., description="Título descriptivo del reporte generado.")
    content: str = Field(
        ...,
        description="Contenido completo del reporte en formato texto/markdown.",
    )
    sections: list[dict] = Field(
        ...,
        description=(
            "Lista de secciones del reporte. Cada elemento es un dict con "
            "las claves 'title' (str) y 'content' (str)."
        ),
    )
    model: str = Field(..., description="Identificador del modelo de IA utilizado.")


class AgentTaskResponse(BaseModel):
    """Respuesta de la ejecución de una tarea por un agente de IA."""

    result: str = Field(
        ...,
        description="Resultado final de la tarea ejecutada por el agente.",
    )
    steps_taken: int = Field(
        ...,
        description="Número de pasos/iteraciones que realizó el agente para completar la tarea.",
        ge=0,
    )
    model: str = Field(..., description="Identificador del modelo de IA utilizado.")
