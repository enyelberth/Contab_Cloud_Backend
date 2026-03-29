from app.database import init_db_from_sql


def run_seed():
    """Carga el esquema y datos demo definidos en db/schema.sql."""
    init_db_from_sql()
    print("Seed ejecutado: esquema + datos demo aplicados")


if __name__ == "__main__":
    run_seed()
