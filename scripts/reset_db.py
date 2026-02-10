"""
Reset Database Script - DROPS AND RECREATES TABLES
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.settings import get_logger
from src.db import engine, init_db
from src.models import Base

logger = get_logger(__name__)


def reset_db():
    logger.info("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Tables dropped")

    logger.info("Creating new tables...")
    init_db()
    logger.info("Tables created successfully")


if __name__ == "__main__":
    try:
        reset_db()
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        sys.exit(1)
