"""
Knowledge Services: RAG and LLM
Consolidated from src/backend/rag_service_v2.py and src/backend/support_service.py
"""
import pickle
import httpx
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from datetime import datetime

from .config import settings, get_logger

logger = get_logger(__name__)

# ============================================================================
# RAG SERVICE (BM25)
# ============================================================================

class RAGService:
    """
    Lightweight RAG Service using BM25
    """
    def __init__(self):
        self.docs_path = Path("docs")
        self.index_path = Path("data/vector_store/index_bm25.pkl")
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100
        )
        
        self.bm25 = None
        self.chunks = []
        self._load_or_create_index()

    def _load_or_create_index(self):
        """Load keyword index or create it from docs"""
        try:
            if self.index_path.exists():
                with open(self.index_path, 'rb') as f:
                    data = pickle.load(f)
                    self.bm25 = data['bm25']
                    self.chunks = data['chunks']
                logger.info("bm25_index_loaded", chunks=len(self.chunks))
            else:
                self.rebuild_index()
        except Exception as e:
            logger.error("index_init_error", error=str(e))
            self.rebuild_index()

    def rebuild_index(self):
        """Force rebuild of keyword index from documents"""
        logger.info("rebuilding_bm25_index")
        documents = self._load_documents()
        if not documents:
            logger.warning("no_documents_found")
            return
            
        self.chunks = self.text_splitter.split_documents(documents)
        tokenized_corpus = [doc.page_content.lower().split() for doc in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        with open(self.index_path, 'wb') as f:
            pickle.dump({'bm25': self.bm25, 'chunks': self.chunks}, f)
        
        logger.info("bm25_index_created", chunks=len(self.chunks))

    def _load_documents(self) -> List[Document]:
        """Load all documents from docs folder"""
        documents = []
        loaders = {'.pdf': PyPDFLoader, '.txt': TextLoader, '.docx': Docx2txtLoader, '.md': TextLoader}
        
        for doc_path in self.docs_path.rglob("*"):
            if not doc_path.is_file() or doc_path.name.startswith('.'): continue
            loader_class = loaders.get(doc_path.suffix.lower())
            if not loader_class: continue
            
            try:
                loader = loader_class(str(doc_path))
                docs = loader.load()
                for d in docs:
                    d.metadata.update({'source': str(doc_path.relative_to(self.docs_path))})
                documents.extend(docs)
                logger.info("doc_loaded", path=str(doc_path))
            except Exception as e:
                logger.error("doc_load_error", path=str(doc_path), error=str(e))
        return documents

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant text using BM25 keyword matching"""
        if not self.bm25 or not self.chunks:
            return []
            
        try:
            tokenized_query = query.lower().split()
            top_n_docs = self.bm25.get_top_n(tokenized_query, self.chunks, n=k)
            
            results = []
            for doc in top_n_docs:
                results.append({
                    'content': doc.page_content,
                    'source': doc.metadata.get('source', 'unknown')
                })
            return results
        except Exception as e:
            logger.error("rag_retrieval_error", error=str(e))
            return []

    def get_context_for_llm(self, query: str, k: int = 3) -> str:
        """Format context for LLM prompt"""
        docs = self.retrieve(query, k=k)
        if not docs:
            return "No se encontró información relevante en los manuales."
            
        parts = [f"[Ref: {d['source']}]\n{d['content']}" for d in docs]
        return "\n\n".join(parts)

rag_service = RAGService()

# ============================================================================
# SUPPORT SERVICE (LLM)
# ============================================================================

class SupportService:
    """
    Service to handle ISP technical support using RAG + LLM
    """
    def __init__(self):
        self.groq_api_key = settings.groq_api_key
        self.groq_model = settings.groq_model or "llama-3.3-70b-versatile"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.rag_service = rag_service

    async def get_ai_response(self, user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
        """Process query using RAG + Groq LLM"""
        if not self.groq_api_key:
            return "Lo siento, el servicio de IA no está configurado actualmente."
        
        # 1. RETRIEVE CONTEXT
        context = self.rag_service.get_context_for_llm(user_query, k=3)
        logger.info("rag_context_retrieved", query=user_query[:50], has_context=bool(context))
        
        # 2. BUILD SYSTEM PROMPT
        system_prompt = self._build_system_prompt(context)
        
        # 3. BUILD MESSAGES
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history[-4:])
        messages.append({"role": "user", "content": user_query})
        
        # 4. LLM GENERATION
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.groq_model,
                        "messages": messages,
                        "temperature": 0.5,
                        "max_tokens": 512
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data["choices"][0]["message"]["content"]
                    logger.info("llm_response_generated", query=user_query[:50])
                    return answer
                else:
                    logger.error("groq_api_error", status_code=response.status_code)
                    return "Lo siento, tuve un problema al procesar su solicitud."
                    
        except Exception as e:
            logger.error("support_service_error", error=str(e))
            return "Lo siento, ocurrió un error técnico. Por favor intente de nuevo."

    def _build_system_prompt(self, context: str) -> str:
        """Build formal system prompt with RAG context"""
        return f"""Eres el Asistente Virtual Especializado de soporte técnico para un Proveedor de Internet (ISP).
Tu objetivo es brindar asistencia técnica profesional, cortés y eficiente.

CONTEXTO DE LA BASE DE CONOCIMIENTO:
{context}

REGLAS DE TONO Y PROFESIONALISMO:
1. 🤵 **Trato Formal**: Dirígete siempre al cliente de "Usted". Mantén un tono corporativo y respetuoso en todo momento.
2. 🛡️ **Privacidad de Información**: NO uses códigos internos, etiquetas de categorías técnicas (ej. "Tipo de visita: Emergencia") o términos que parezcan de un manual interno.
3. 📝 **Claridad**: Traduce la información técnica a un lenguaje que el cliente entienda, sin perder la precisión.
4. 🏢 **Identidad**: Habla en nombre de la empresa ("En nuestra empresa...", "Nuestro equipo técnico...").

INSTRUCCIONES CRÍTICAS:
1. 🎯 **Fidelidad**: Responde ÚNICAMENTE basado en el contexto proporcionado.
2. ❌ **No Inventar**: Si algo no está en el contexto, indica amablemente que transferirás la consulta a un agente humano.
3. 🇪🇸 **Idioma**: Responde siempre en español profesional.
4. 🔧 **Soluciones**: Proporciona pasos de solución claros y numerados cuando sea pertinente.

PROHIBIDO:
- Usar términos como "llamar a la puerta", "chatear", o lenguaje coloquial.
- Prometer tiempos exactos de llegada; usa rangos estimados según la política.
- Mencionar procedimientos de configuración interna de servidores o redes troncales."""

support_service = SupportService()
