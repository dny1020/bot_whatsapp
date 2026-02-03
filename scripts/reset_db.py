"""
Reset Database Script - DROPS AND RECREATES TABLES
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import engine, init_db
from src.models import Base


def reset_db():
    print("⚠️ Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables dropped.")

    print("🔨 Creating new tables...")
    init_db()
    print("✅ Tables created successfully.")


if __name__ == "__main__":
    try:
        reset_db()
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        sys.exit(1)
