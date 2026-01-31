#!/usr/bin/env python3
"""
Script to update RAG vector store
Run this after adding/updating documents in docs/
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backend.rag_service_v2 import rag_service
from src.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Update vector store from documents"""
    print("🔄 Actualizando vector store...")
    print()
    
    try:
        # Count documents
        docs_count = rag_service._count_documents()
        print(f"📚 Documentos encontrados: {docs_count}")
        
        if docs_count == 0:
            print("⚠️  No se encontraron documentos en docs/")
            print("   Agrega archivos .pdf, .txt, .docx o .md")
            return 1
        
        # Update vector store
        print("🔨 Procesando documentos...")
        rag_service.update_vector_store()
        
        print()
        print("✅ Vector store actualizado exitosamente!")
        print(f"📍 Ubicación: {rag_service.vector_store_path}")
        
        # Test retrieval
        print()
        print("🧪 Probando recuperación...")
        test_query = "problema de internet"
        results = rag_service.retrieve(test_query, k=2)
        
        if results:
            print(f"✅ Recuperación funcionando ({len(results)} resultados)")
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['source']} ({result['type']})")
        else:
            print("⚠️  No se pudieron recuperar resultados de prueba")
        
        return 0
        
    except Exception as e:
        logger.error("update_failed", error=str(e))
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
