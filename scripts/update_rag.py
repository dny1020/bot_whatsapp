"""
Update RAG Index Script
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.rag import rag_service

if __name__ == "__main__":
    print("Rebuilding RAG index (BM25)...")
    try:
        rag_service.rebuild_index()
        print("✅ Index rebuilt successfully.")
    except Exception as e:
        print(f"❌ Error rebuilding index: {e}")
        sys.exit(1)
