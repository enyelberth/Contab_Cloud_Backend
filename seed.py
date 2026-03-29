from app.database import init_db_migrations


def run_seed():
    """Aplica migraciones SQL versionadas y datos demo idempotentes."""
    init_db_migrations()
    print("Seed ejecutado: migraciones + datos demo aplicados")


if __name__ == "__main__":
    run_seed()
