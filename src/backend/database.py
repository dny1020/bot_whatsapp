"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Create engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("database_error", error=str(e))
        raise
    finally:
        db.close()


def init_db():
    """Initialize database"""
    from .models import Base
    from sqlalchemy import text
    
    try:
        # Create ENUM type if not exists (Postgres-specific)
        # This prevents "duplicate key value violates unique constraint" error
        # when multiple workers try to create the ENUM simultaneously
        with engine.connect() as conn:
            conn.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE conversationstatus AS ENUM ('active', 'idle', 'closed', 'archived');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            conn.commit()
        
        # Create tables (checkfirst=True checks if tables exist)
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_error", error=str(e))
        # Don't raise - allow app to start even if initialization fails

