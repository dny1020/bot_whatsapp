"""
Reset Database Script - DROPS AND RECREATES TABLES
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import engine, Base, init_db

def reset_db():
    print("  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print(" Tables dropped.")
    
    print(" Creating new tables...")
    init_db()
    print(" Tables created successfully.")

if __name__ == "__main__":
    try:
        reset_db()
    except Exception as e:
        print(f" Error resetting database: {e}")
        sys.exit(1)
