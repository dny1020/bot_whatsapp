#!/usr/bin/env python3
"""
Script to load documents (PDF, TXT, MD) into knowledge base
Usage: python scripts/load_documents.py path/to/documents/
"""
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.pdf_loader import document_loader
from src.backend.rag_service import rag_service


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/load_documents.py <path_to_documents>")
        print("\nExamples:")
        print("  python scripts/load_documents.py docs/manual.pdf")
        print("  python scripts/load_documents.py docs/")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    if not input_path.exists():
        print(f"Error: Path not found: {input_path}")
        sys.exit(1)
    
    print(f"Loading documents from: {input_path}")
    
    # Load documents
    if input_path.is_file():
        if input_path.suffix == ".pdf":
            entries = document_loader.load_pdf(input_path)
        else:
            entries = document_loader.load_text_file(input_path)
    else:
        entries = document_loader.load_directory(input_path)
    
    print(f"\n✅ Loaded {len(entries)} entries")
    
    # Add to RAG service
    for entry in entries:
        rag_service.knowledge_base.append(entry)
    
    # Save to file
    rag_service.save_knowledge_base()
    
    print(f"✅ Knowledge base saved to config/knowledge_base.json")
    print(f"📊 Total entries in knowledge base: {len(rag_service.knowledge_base)}")


if __name__ == "__main__":
    main()
