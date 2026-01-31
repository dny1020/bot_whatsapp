"""
Reset Database Script
DROPS ALL TABLES and recreates them.
Use with caution.
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backend.database import engine
from src.backend.models import Base

def reset_db():
    print("  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print(" Tables dropped.")
    
    print(" Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print(" Tables created successfully.")
    
    print("\nSchema updated:")
    for table in Base.metadata.sorted_tables:
        print(f" - {table.name}")

if __name__ == "__main__":
    try:
        reset_db()
    except Exception as e:
        print(f" Error resetting database: {e}")
        sys.exit(1)
