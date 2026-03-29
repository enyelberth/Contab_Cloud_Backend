from app.database import execute, fetch_one, get_connection, release_connection
from decimal import Decimal


def run_seed():
    db = get_connection()
    try:
        # 1. Crear Sedes (Branches)
        if not fetch_one(db, "SELECT id FROM branches LIMIT 1"):
            execute(
                db,
                """
                INSERT INTO branches (name, address, phone, is_active)
                VALUES (%s, %s, %s, %s)
                """,
                ("Sede Principal Barquisimeto", "Av. Venezuela con Calle 12", "0251-1234567", True),
            )
            print("✅ Sede creada.")

        # 2. Crear Roles
        if not fetch_one(db, "SELECT id FROM roles LIMIT 1"):
            execute(
                db,
                """
                INSERT INTO roles (name, description)
                VALUES (%s, %s), (%s, %s)
                """,
                (
                    "admin",
                    "Acceso total al sistema",
                    "cajero",
                    "Solo ventas y apertura de caja",
                ),
            )
            print("✅ Roles creados.")

        # 3. Crear Monedas
        if not fetch_one(db, "SELECT id FROM currencies LIMIT 1"):
            execute(
                db,
                """
                INSERT INTO currencies (code, symbol, is_default)
                VALUES (%s, %s, %s), (%s, %s, %s)
                """,
                ("USD", "$", False, "VES", "Bs", True),
            )
            usd = fetch_one(db, "SELECT id FROM currencies WHERE code = %s", ("USD",))

            # 4. Crear una Tasa de Cambio inicial (Ejemplo)
            execute(
                db,
                """
                INSERT INTO exchange_rates (currency_id, rate_value)
                VALUES (%s, %s)
                """,
                (usd["id"], Decimal("36.50")),
            )
            print("✅ Monedas y Tasa inicial creadas.")

        print("🚀 Seed completado con éxito.")

    except Exception as e:
        print(f"❌ Error en el seed: {e}")
        db.rollback()
    finally:
        release_connection(db)

if __name__ == "__main__":
    run_seed()