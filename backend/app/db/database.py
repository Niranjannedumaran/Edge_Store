from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.config import settings
from backend.app.core.logger import logger

from pathlib import Path

# Ensure SQLite storage directory exists before establishing connection
if "sqlite" in settings.DATABASE_URL:
    db_raw = settings.DATABASE_URL.replace("sqlite:////", "/").replace("sqlite:///", "")
    if db_raw and not db_raw.startswith(":memory:"):
        Path(db_raw).parent.mkdir(parents=True, exist_ok=True)

# SQLite connection with connect_args for multithreading
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Enforce foreign key constraints and configure WAL mode in SQLite
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            # Set WAL mode where appropriate
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        except Exception as e:
            logger.warning(f"Could not configure SQLite pragmas: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for database sessions."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
