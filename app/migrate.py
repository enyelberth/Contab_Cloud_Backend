import argparse

from app.database import get_migration_status, run_db_migrations


def command_up() -> None:
    applied = run_db_migrations()
    print(f"Migraciones ejecutadas correctamente. Nuevas aplicadas: {applied}")


def command_status() -> None:
    rows = get_migration_status()
    if not rows:
        print("No hay archivos de migracion en db/migrations")
        return

    print("version | estado | archivo | applied_at")
    print("-" * 100)
    for row in rows:
        print(f"{row['version']} | {row['state']} | {row['name']} | {row['applied_at']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI de migraciones PostgreSQL")
    parser.add_argument(
        "command",
        choices=["up", "status"],
        help="up: aplica migraciones pendientes, status: muestra estado",
    )

    args = parser.parse_args()

    if args.command == "up":
        command_up()
    elif args.command == "status":
        command_status()


if __name__ == "__main__":
    main()
