from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db_from_sql

app = FastAPI(title="ERP Multi-Sede")


@app.on_event("startup")
def startup_event():
    try:
        init_db_from_sql()
    except Exception as exc:
        # Dejamos log explícito para depuración en entorno académico/local.
        print(f"Error al inicializar esquema SQL: {exc}")

from app.branche import router as branche_router
from app.user import router as user_router
from app.role import router as role_router
from app.permissions import router as permissions_router

app.include_router(permissions_router.router)

app.include_router(branche_router.router)
app.include_router(user_router.router, prefix="/sales", tags=["sales"])
app.include_router(role_router.router)


# Registro de Módulos (Incluimos las rutas de cada carpeta)
#app.include_router(auth_router, prefix="/auth", tags=["Seguridad"])
#app.include_router(inventory_router, prefix="/inventory", tags=["Inventario"])

@app.get("/")
def home():
    return {"message": "Sistema ERP Funcionando"}