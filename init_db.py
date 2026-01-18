#!/usr/bin/env python3
"""
Database initialization script
"""
import sys
import os

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from backend.database import init_db, engine
from backend.models import Base
from utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Initialize database tables"""
    try:
        logger.info("Initializing database...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully!")
        print("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
