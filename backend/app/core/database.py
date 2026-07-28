"""Database configuration and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session
from app.core.config import settings

# Sync engine
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Base class for models
Base = declarative_base()


def get_db():
    """FastAPI dependency: provides a sync database session"""
    session = Session(sync_engine)
    try:
        yield session
    finally:
        session.close()
