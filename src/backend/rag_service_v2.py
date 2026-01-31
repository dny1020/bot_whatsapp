"""
RAG Service - Sprint 1
Vector-based knowledge retrieval for technical support

Pipeline: Docs → Chunking → Embeddings → FAISS → Retrieval → LLM Response
Uses HuggingFace sentence-transformers for FREE local embeddings (no API costs)
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    Docx2txtLoader,
    UnstructuredMarkdownLoader
)
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """
    RAG Service for document-based Q&A
    👉 ONLY active in SOPORTE state
    👉 Returns context + LLM generated answer
    👉 Uses FREE local embeddings (HuggingFace)
    """
    
    def __init__(self):
        self.docs_path = Path("docs")
        self.vector_store_path = Path("data/vector_store")
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize HuggingFace embeddings (FREE, local)
        # Model: all-MiniLM-L6-v2 (384 dims, 22M params, fast)
        # Alternative: all-mpnet-base-v2 (768 dims, better quality, slower)
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("embeddings_initialized", model="all-MiniLM-L6-v2")
        except Exception as e:
            logger.error("embeddings_init_error", error=str(e))
            self.embeddings = None

        
        # Text splitter (500-800 tokens)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.vector_store = None
        
        # Only load vector store if embeddings initialized successfully
        if self.embeddings:
            self._load_or_create_vector_store()
            logger.info("rag_service_initialized", 
                       docs_loaded=self._count_documents(),
                       vector_store_exists=self.vector_store is not None)
        else:
            logger.warning("rag_service_disabled", reason="embeddings_failed")

    
    def _count_documents(self) -> int:
        """Count documents in docs directory"""
        count = 0
        for ext in ['*.pdf', '*.txt', '*.docx', '*.md']:
            count += len(list(self.docs_path.rglob(ext)))
        return count
    
    def _get_docs_hash(self) -> str:
        """Get hash of all documents for cache invalidation"""
        hasher = hashlib.md5()
        
        for doc_path in sorted(self.docs_path.rglob("*")):
            if doc_path.is_file() and not doc_path.name.startswith('.'):
                hasher.update(str(doc_path.stat().st_mtime).encode())
        
        return hasher.hexdigest()
    
    def _load_or_create_vector_store(self):
        """Load existing vector store or create new one"""
        try:
            # Check if vector store exists and is up to date
            vector_store_file = self.vector_store_path / "index.faiss"
            hash_file = self.vector_store_path / "docs_hash.txt"
            
            current_hash = self._get_docs_hash()
            
            if vector_store_file.exists() and hash_file.exists():
                stored_hash = hash_file.read_text().strip()
                
                if stored_hash == current_hash:
                    # Load existing vector store
                    self.vector_store = FAISS.load_local(
                        str(self.vector_store_path),
                        self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                    logger.info("vector_store_loaded", path=str(self.vector_store_path))
                    return
            
            # Create new vector store
            logger.info("creating_new_vector_store")
            self._create_vector_store()
            
            # Save hash
            hash_file.write_text(current_hash)
            
        except Exception as e:
            logger.error("vector_store_init_error", error=str(e))
            self.vector_store = None
    
    def _load_documents(self) -> List[Document]:
        """Load all documents from docs directory"""
        documents = []
        
        loaders = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.docx': Docx2txtLoader,
            '.md': UnstructuredMarkdownLoader
        }
        
        for doc_path in self.docs_path.rglob("*"):
            if not doc_path.is_file() or doc_path.name.startswith('.'):
                continue
            
            ext = doc_path.suffix.lower()
            loader_class = loaders.get(ext)
            
            if not loader_class:
                continue
            
            try:
                loader = loader_class(str(doc_path))
                docs = loader.load()
                
                # Add metadata
                for doc in docs:
                    doc.metadata.update({
                        'source': str(doc_path.relative_to(self.docs_path)),
                        'type': doc_path.parent.name,
                        'filename': doc_path.name
                    })
                
                documents.extend(docs)
                logger.info("document_loaded", path=str(doc_path), chunks=len(docs))
                
            except Exception as e:
                logger.error("document_load_error", path=str(doc_path), error=str(e))
        
        return documents
    
    def _create_vector_store(self):
        """Create vector store from documents"""
        # Load documents
        documents = self._load_documents()
        
        if not documents:
            logger.warning("no_documents_found", path=str(self.docs_path))
            return
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        logger.info("documents_chunked", total_chunks=len(chunks))
        
        # Create vector store
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        
        # Save to disk
        self.vector_store.save_local(str(self.vector_store_path))
        logger.info("vector_store_created", chunks=len(chunks))
    
    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve top-K relevant documents
        
        Args:
            query: User question
            k: Number of results to return
            
        Returns:
            List of relevant documents with content and metadata
        """
        if not self.vector_store:
            logger.warning("vector_store_not_available")
            return []
        
        try:
            # Retrieve relevant documents
            docs = self.vector_store.similarity_search(query, k=k)
            
            results = []
            for doc in docs:
                results.append({
                    'content': doc.page_content,
                    'source': doc.metadata.get('source', 'unknown'),
                    'type': doc.metadata.get('type', 'unknown')
                })
            
            logger.info("rag_retrieval", query=query[:50], results=len(results))
            return results
            
        except Exception as e:
            logger.error("rag_retrieval_error", query=query[:50], error=str(e))
            return []
    
    def get_context_for_llm(self, query: str, k: int = 3) -> str:
        """
        Get formatted context for LLM prompt
        
        Args:
            query: User question
            k: Number of documents to retrieve
            
        Returns:
            Formatted context string
        """
        docs = self.retrieve(query, k=k)
        
        if not docs:
            return "No se encontró información relevante en la base de conocimiento."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[Documento {i} - {doc['source']}]\n{doc['content']}")
        
        return "\n\n".join(context_parts)
    
    def update_vector_store(self):
        """Force update of vector store"""
        logger.info("force_updating_vector_store")
        self._create_vector_store()
        
        # Update hash
        hash_file = self.vector_store_path / "docs_hash.txt"
        hash_file.write_text(self._get_docs_hash())


# Global RAG service instance
rag_service = RAGService()
