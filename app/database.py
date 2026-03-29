from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError # Importante para capturar errores de conexión

# 1. Cargamos las variables de entorno
load_dotenv()

# 2. Configuración de la URL
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://enyelberth:30204334@localhost:5432/erp" # Corregido el { que tenías antes
)

# 3. El Engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10, 
    max_overflow=20
)

# 4. SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. Base
Base = declarative_base()

# 6. Dependencia get_db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- NUEVA SECCIÓN PARA MENSAJE POR TERMINAL ---

def init_db():
    try:
        # Esto busca todas las clases que heredan de 'Base' y crea las tablas
        # Solo se crearán si no existen previamente.
        Base.metadata.create_all(bind=engine)
        print("✅ ¡Conexión exitosa! Las tablas de 'Kaizen ERP' han sido verificadas/creadas.")
    except OperationalError as e:
        print("❌ Error: No se pudo conectar a la base de datos.")
        print(f"Detalle: {e}")
    except Exception as e:
        print(f"⚠️ Ocurrió un error inesperado: {e}")

# Esto permite que si ejecutas 'python database.py' directamente, se cree la BD
if __name__ == "__main__":
    init_db()