import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Attempt to initialize engine if DATABASE_URL is provided
engine = None
SessionLocal = None
database_connected = False

if settings.DATABASE_URL:
    try:
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5}
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        database_connected = True
        logger.info("Successfully connected to the PostgreSQL database.")
    except Exception as e:
        logger.warning(
            f"Failed to connect to the database specified in DATABASE_URL: {e}. "
            f"Falling back to CSV-first data ingestion."
        )
        engine = None
        SessionLocal = None
        database_connected = False
else:
    logger.info("DATABASE_URL not set. Operating in CSV-first ingestion mode.")


def get_db() -> Generator:
    """
    Dependency to get a database session.
    If database is not connected, yields None.
    """
    if not database_connected or SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_status() -> dict:
    """
    Checks the status of the database connection.
    """
    if not database_connected or engine is None:
        return {"connected": False, "details": "No active database connection. Falling back to CSV files."}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"connected": True, "details": "Successfully connected to PostgreSQL database."}
    except Exception as e:
        return {"connected": False, "details": f"Database URL provided but connection failed: {str(e)}"}
