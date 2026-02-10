"""
Update RAG Index Script
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.settings import get_logger
from src.services.rag import rag_service

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("Rebuilding RAG index (BM25)...")
    try:
        rag_service.rebuild_index()
        logger.info("Index rebuilt successfully")
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
        sys.exit(1)
