"""
Conexión a base de datos SQLite
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .settings import DATABASE_URL, DEBUG, get_logger

logger = get_logger(__name__)

# Crear directorio data si no existe
os.makedirs("./data", exist_ok=True)

# Crear engine de SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=DEBUG,
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Obtener sesión de base de datos para FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Obtener sesión de base de datos (uso manual)"""
    return SessionLocal()


def init_db():
    """Inicializar tablas de la base de datos"""
    from .models import Base
    
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info(f"Base de datos inicializada: {DATABASE_URL}")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
