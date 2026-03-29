from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import models

print("--- Iniciando verificación de Base de Datos ---")
try:
    models.Base.metadata.create_all(bind=engine)
    print("✅ Proceso de metadata.create_all finalizado sin errores.")
except Exception as e:
    print(f"❌ Error durante la creación: {e}")
app = FastAPI(title="ERP Multi-Sede")

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