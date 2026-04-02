import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db_migrations
from app.request_context import reset_request_meta, set_request_meta

app = FastAPI(title="ERP Multi-Sede")


@app.on_event("startup")
def startup_event():
    try:
        init_db_migrations()
    except Exception as exc:
        # Dejamos log explícito para depuración en entorno académico/local.
        print(f"Error al inicializar migraciones SQL: {exc}")


@app.middleware("http")
async def request_metadata_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    forwarded_for = request.headers.get("X-Forwarded-For")
    ip_address = (
        forwarded_for.split(",")[0].strip()
        if forwarded_for
        else (request.client.host if request.client else None)
    )

    token = set_request_meta(
        {
            "request_id": request_id,
            "ip_address": ip_address,
            "endpoint": request.url.path,
            "http_method": request.method,
        }
    )

    try:
        response = await call_next(request)
    finally:
        reset_request_meta(token)

    response.headers["X-Request-ID"] = request_id
    return response

from app.branche import router as branche_router
from app.user import router as user_router
from app.role import router as role_router
from app.permissions import router as permissions_router
from app.company import router as company_router
from app.access import router as access_router
from app.auth import router as auth_router
from app.prueba import router as prueba_router
from app.cuentas import router as cuentas_router

app.include_router(auth_router.router)
app.include_router(permissions_router.router)
app.include_router(company_router.router)
app.include_router(access_router.router)

app.include_router(branche_router.router)
app.include_router(user_router.router, prefix="/sales", tags=["sales"])
app.include_router(role_router.router)
app.include_router(prueba_router.router)
app.include_router(cuentas_router.router)


# Registro de Módulos (Incluimos las rutas de cada carpeta)
#app.include_router(auth_router, prefix="/auth", tags=["Seguridad"])
#app.include_router(inventory_router, prefix="/inventory", tags=["Inventario"])

@app.get("/")
def home():
    return {"message": "Sistema ERP Funcionando"}