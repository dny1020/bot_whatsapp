"""
Database Engine and Session Management
"""

from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from .settings import settings, get_logger

logger = get_logger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """FastAPI dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database session with auto-commit"""
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


def init_db() -> None:
    """Initialize database tables"""
    from .models import Base

    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                DO $$ BEGIN
                    CREATE TYPE conversationstatus AS ENUM ('active', 'idle', 'closed', 'archived');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
            )
            conn.commit()

        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_error", error=str(e))
