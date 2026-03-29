from app.database import SessionLocal, engine
from app import models
from decimal import Decimal

def run_seed():
    db = SessionLocal()
    try:
        # 1. Crear Sedes (Branches)
        if not db.query(models.Branch).first():
            sede_principal = models.Branch(
                name="Sede Principal Barquisimeto",
                address="Av. Venezuela con Calle 12",
                phone="0251-1234567"
            )
            db.add(sede_principal)
            print("✅ Sede creada.")

        # 2. Crear Roles
        if not db.query(models.Role).first():
            admin_role = models.Role(name="admin", description="Acceso total al sistema")
            cajero_role = models.Role(name="cajero", description="Solo ventas y apertura de caja")
            db.add_all([admin_role, cajero_role])
            print("✅ Roles creados.")

        # 3. Crear Monedas
        if not db.query(models.Currency).first():
            usd = models.Currency(code="USD", symbol="$", is_default=False)
            ves = models.Currency(code="VES", symbol="Bs", is_default=True)
            db.add_all([usd, ves])
            db.flush() # Para obtener los IDs de las monedas

            # 4. Crear una Tasa de Cambio inicial (Ejemplo)
            tasa = models.ExchangeRate(
                currency_id=usd.id, 
                rate_value=Decimal("36.50")
            )
            db.add(tasa)
            print("✅ Monedas y Tasa inicial creadas.")

        # Guardar todo en la BD
        db.commit()
        print("🚀 Seed completado con éxito.")

    except Exception as e:
        print(f"❌ Error en el seed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()