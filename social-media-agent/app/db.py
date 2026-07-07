"""
Database setup: SQLAlchemy engine + session factory.

SQLite by default (data/app.db). Set DATABASE_URL to move to Postgres later —
no other code changes needed.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DEFAULT_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(DEFAULT_DB_DIR, 'app.db')}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables and seed the two brands. Idempotent."""
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    from app import models  # noqa: F401 — register tables
    Base.metadata.create_all(engine)

    from app.seed import seed_brands
    db = SessionLocal()
    try:
        seed_brands(db)
    finally:
        db.close()
