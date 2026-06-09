"""Manejo de sesiones de base de datos para dependencias FastAPI."""

from app.core.db.database import SessionLocal

def get_db():
    """Entrega una sesion SQLAlchemy y garantiza su cierre al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
