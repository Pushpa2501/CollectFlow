
from sqlalchemy import inspect, text

from backend.database.connection import Base, engine
import backend.models  # Register SQLAlchemy models


def initialize_database():
    """Create registered tables and verify database constraints."""

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    print("\n=== COLLECTFLOW DATABASE INITIALIZATION ===")

    tables = sorted(inspector.get_table_names())

    for table in tables:
        print(f"\nTable: {table}")

        columns = inspector.get_columns(table)
        primary_keys = inspector.get_pk_constraint(table)

        print("  Columns:", len(columns))
        print("  Primary Key:",
              primary_keys.get("constrained_columns"))

        foreign_keys = inspector.get_foreign_keys(table)

        for fk in foreign_keys:
            print(
                "  Foreign Key:",
                fk["constrained_columns"],
                "->",
                fk["referred_table"],
                fk["referred_columns"]
            )

    with engine.connect() as connection:
        foreign_keys_enabled = connection.execute(
            text("PRAGMA foreign_keys")
        ).scalar()

        print("\nForeign Key Enforcement:",
              foreign_keys_enabled)

        if foreign_keys_enabled != 1:
            raise RuntimeError(
                "SQLite foreign-key enforcement is disabled"
            )

    print("\nDatabase initialization successful!")


if __name__ == "__main__":
    initialize_database()
