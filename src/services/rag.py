"""
Servicio RAG - Búsqueda BM25
"""

import os
import pickle

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from rank_bm25 import BM25Okapi

from ..settings import get_logger

logger = get_logger(__name__)

# Rutas
DOCS_PATH = "docs"
INDEX_PATH = "data/vector_store/index_bm25.pkl"

# Variables globales para el índice
_bm25 = None
_chunks = []


def _load_documents():
    """Cargar todos los documentos de la carpeta docs"""
    documents = []
    
    loaders = {
        ".pdf": PyPDFLoader,
        ".txt": TextLoader,
        ".docx": Docx2txtLoader,
        ".md": TextLoader,
    }

    if not os.path.exists(DOCS_PATH):
        return documents

    for root, dirs, files in os.walk(DOCS_PATH):
        for filename in files:
            if filename.startswith("."):
                continue
                
            filepath = os.path.join(root, filename)
            ext = os.path.splitext(filename)[1].lower()
            
            loader_class = loaders.get(ext)
            if not loader_class:
                continue

            try:
                loader = loader_class(filepath)
                docs = loader.load()
                
                for doc in docs:
                    doc.metadata["source"] = os.path.relpath(filepath, DOCS_PATH)
                
                documents.extend(docs)
                logger.info(f"Documento cargado: {filepath}")
            except Exception as e:
                logger.error(f"Error cargando {filepath}: {e}")

    return documents


def rebuild_index():
    """Reconstruir índice BM25"""
    global _bm25, _chunks
    
    logger.info("Reconstruyendo índice BM25...")
    
    documents = _load_documents()
    if not documents:
        logger.warning("No se encontraron documentos")
        return

    # Dividir en chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    _chunks = splitter.split_documents(documents)
    
    # Crear índice BM25
    tokenized_corpus = [doc.page_content.lower().split() for doc in _chunks]
    _bm25 = BM25Okapi(tokenized_corpus)

    # Guardar índice
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"bm25": _bm25, "chunks": _chunks}, f)

    logger.info(f"Índice creado con {len(_chunks)} chunks")


def _load_index():
    """Cargar índice existente o crear uno nuevo"""
    global _bm25, _chunks
    
    try:
        if os.path.exists(INDEX_PATH):
            with open(INDEX_PATH, "rb") as f:
                data = pickle.load(f)
                _bm25 = data["bm25"]
                _chunks = data["chunks"]
            logger.info(f"Índice cargado con {len(_chunks)} chunks")
        else:
            rebuild_index()
    except Exception as e:
        logger.error(f"Error cargando índice: {e}")
        rebuild_index()


def search(query, k=3):
    """Buscar documentos relevantes"""
    global _bm25, _chunks
    
    if _bm25 is None:
        _load_index()
    
    if not _bm25 or not _chunks:
        return []

    try:
        tokenized_query = query.lower().split()
        top_docs = _bm25.get_top_n(tokenized_query, _chunks, n=k)

        results = []
        for doc in top_docs:
            results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
            })
        return results
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        return []


def get_context_for_query(query, k=3):
    """Obtener contexto formateado para el LLM"""
    docs = search(query, k=k)

    if not docs:
        return "No se encontró información relevante en los manuales."

    parts = []
    for doc in docs:
        parts.append(f"[Ref: {doc['source']}]\n{doc['content']}")
    
    return "\n\n".join(parts)


# Cargar índice al importar
_load_index()
