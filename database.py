"""Database configuration shared by the app, migrations, and import tools."""
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base


def database_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgres://")
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    if url:
        return url
    if os.environ.get("FLASK_ENV") == "production":
        raise RuntimeError("DATABASE_URL is required in production; local SQLite is not production storage.")
    return os.environ.get("DEV_DATABASE_URL", "sqlite:///data/sudana-dev.db")


engine = create_engine(database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_development_schema():
    """For local development only; production uses Alembic migrations."""
    Base.metadata.create_all(engine)
