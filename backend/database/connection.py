
import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Default SQLite database location
DATABASE_DIR = BASE_DIR / "data"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DATABASE_PATH = DATABASE_DIR / "collectflow.db"

# Optional override for isolated reproducibility tests.
# Existing behavior remains unchanged when the variable is absent.
database_override = os.environ.get("COLLECTFLOW_DATABASE_PATH")

DATABASE_PATH = (
    Path(database_override).expanduser().resolve()
    if database_override
    else DEFAULT_DATABASE_PATH
)

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


# Enable SQLite foreign-key enforcement
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Database session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass


def get_db():
    """Provide a database session for FastAPI requests."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
