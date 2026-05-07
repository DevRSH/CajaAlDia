"""Conexión SQLite y sesión SQLAlchemy."""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Usar PostgreSQL en producción (Railway), SQLite en desarrollo local
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Railway usa postgres://, SQLAlchemy necesita postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    # Producción: PostgreSQL (Railway)
    engine = create_engine(DATABASE_URL, echo=False)
else:
    # Desarrollo: SQLite
    DB_PATH = Path(__file__).resolve().parent.parent / "cajaaldia.db"
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    # check_same_thread=False: permitido aquí porque FastAPI ejecuta solicitudes sincrónicas por worker
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base declarativa para modelos."""

    pass


def get_db():
    """Dependencia FastAPI que entrega sesión y la cierra."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
