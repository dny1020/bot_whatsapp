"""
RAG Service - BM25 Keyword Search
"""

import pickle
from pathlib import Path
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from ..settings import get_logger

logger = get_logger(__name__)


class RAGService:
    """Lightweight RAG using BM25 keyword matching"""

    def __init__(self):
        self.docs_path = Path("docs")
        self.index_path = Path("data/vector_store/index_bm25.pkl")
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700, chunk_overlap=100
        )

        self.bm25: BM25Okapi | None = None
        self.chunks: List[Document] = []
        self._load_or_create_index()

    def _load_or_create_index(self) -> None:
        """Load existing index or create new one"""
        try:
            if self.index_path.exists():
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                    self.bm25 = data["bm25"]
                    self.chunks = data["chunks"]
                logger.info("bm25_index_loaded", chunks=len(self.chunks))
            else:
                self.rebuild_index()
        except Exception as e:
            logger.error("index_init_error", error=str(e))
            self.rebuild_index()

    def rebuild_index(self) -> None:
        """Force rebuild index from documents"""
        logger.info("rebuilding_bm25_index")
        documents = self._load_documents()

        if not documents:
            logger.warning("no_documents_found")
            return

        self.chunks = self.text_splitter.split_documents(documents)
        tokenized_corpus = [doc.page_content.lower().split() for doc in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

        with open(self.index_path, "wb") as f:
            pickle.dump({"bm25": self.bm25, "chunks": self.chunks}, f)

        logger.info("bm25_index_created", chunks=len(self.chunks))

    def _load_documents(self) -> List[Document]:
        """Load all documents from docs folder"""
        documents = []
        loaders = {
            ".pdf": PyPDFLoader,
            ".txt": TextLoader,
            ".docx": Docx2txtLoader,
            ".md": TextLoader,
        }

        for doc_path in self.docs_path.rglob("*"):
            if not doc_path.is_file() or doc_path.name.startswith("."):
                continue

            loader_class = loaders.get(doc_path.suffix.lower())
            if not loader_class:
                continue

            try:
                loader = loader_class(str(doc_path))
                docs = loader.load()
                for d in docs:
                    d.metadata["source"] = str(doc_path.relative_to(self.docs_path))
                documents.extend(docs)
                logger.info("doc_loaded", path=str(doc_path))
            except Exception as e:
                logger.error("doc_load_error", path=str(doc_path), error=str(e))

        return documents

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks using BM25"""
        if not self.bm25 or not self.chunks:
            return []

        try:
            tokenized_query = query.lower().split()
            top_n_docs = self.bm25.get_top_n(tokenized_query, self.chunks, n=k)

            return [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                }
                for doc in top_n_docs
            ]
        except Exception as e:
            logger.error("rag_retrieval_error", error=str(e))
            return []

    def get_context_for_llm(self, query: str, k: int = 3) -> str:
        """Format retrieved context for LLM prompt"""
        docs = self.retrieve(query, k=k)

        if not docs:
            return "No se encontró información relevante en los manuales."

        parts = [f"[Ref: {d['source']}]\n{d['content']}" for d in docs]
        return "\n\n".join(parts)


rag_service = RAGService()
