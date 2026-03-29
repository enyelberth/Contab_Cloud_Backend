from contextvars import ContextVar


_request_meta_ctx: ContextVar[dict | None] = ContextVar("request_meta", default=None)


def set_request_meta(meta: dict):
    return _request_meta_ctx.set(meta)


def get_request_meta() -> dict:
    return _request_meta_ctx.get() or {}


def reset_request_meta(token):
    _request_meta_ctx.reset(token)
