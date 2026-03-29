import json

from app.database import execute
from app.request_context import get_request_meta


def log_audit(
    db,
    *,
    actor_user_id: int | None,
    company_id: int | None,
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
        INSERT INTO audit_logs (
            actor_user_id, company_id, module, action,
            entity_type, entity_id, before_data, after_data,
            ip_address, endpoint, http_method, request_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s)
        """,
        (
            actor_user_id,
            company_id,
            module,
            action,
            entity_type,
            str(entity_id) if entity_id is not None else None,
            json.dumps(before_data) if before_data is not None else None,
            json.dumps(after_data) if after_data is not None else None,
            request_meta.get("ip_address"),
            request_meta.get("endpoint"),
            request_meta.get("http_method"),
            request_meta.get("request_id"),
        ),
        returning=False,
    )
