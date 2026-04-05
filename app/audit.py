import json
from datetime import datetime, date

from app.database import execute
from app.request_context import get_request_meta


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def log_audit(
    db,
    *,
    actor_user_id: str | None,
    company_id: str | None,
    module: str,
    action: str,
    entity_type: str,
    entity_id: int | str | None,
    before_data: dict | None = None,
    after_data: dict | None = None,
):
    request_meta = get_request_meta()

    execute(
        db,
        """
        INSERT INTO audit.activity_logs (
            tenant_id, user_id, session_id, action,
            resource, resource_id, metadata,
            ip_address, user_agent
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            company_id,
            actor_user_id,
            request_meta.get("request_id"),
            action,
            f"{module}.{entity_type}",
            str(entity_id) if entity_id is not None else None,
            json.dumps(
                {
                    "before": before_data,
                    "after": after_data,
                    "endpoint": request_meta.get("endpoint"),
                    "http_method": request_meta.get("http_method"),
                },
                default=_json_default,
            ),
            request_meta.get("ip_address"),
            None,
        ),
        returning=False,
    )
