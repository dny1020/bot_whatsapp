"""
Support Service - Sprint 1 Enhanced
Uses RAG (vector-based retrieval) for technical support
LLM only generates response from retrieved context
"""
import httpx
from typing import List, Dict, Any, Optional
from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SupportService:
    """
    Service to handle ISP technical support using RAG + LLM
    👉 RAG retrieves relevant docs, LLM only reformulates answer
    """
    
    def __init__(self):
        self.groq_api_key = settings.groq_api_key
        self.groq_model = settings.groq_model or "llama-3.3-70b-versatile"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Import RAG service (lazy to avoid circular imports)
        self.rag_service = None
        self._init_rag()
    
    def _init_rag(self):
        """Initialize RAG service"""
        try:
            from .rag_service_v2 import rag_service
            self.rag_service = rag_service
            logger.info("rag_service_connected")
        except Exception as e:
            logger.error("rag_service_init_error", error=str(e))
            self.rag_service = None

    async def get_ai_response(self, user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
        """
        Process query using RAG + Groq LLM
        
        Pipeline:
        1. Retrieve relevant docs from vector DB (RAG)
        2. Build context-aware prompt
        3. LLM generates answer based on retrieved context
        4. Return formatted response
        """
        if not self.groq_api_key:
            return "Lo siento, el servicio de IA no está configurado actualmente."
        
        # 1. RETRIEVE CONTEXT (RAG)
        context = ""
        if self.rag_service:
            try:
                context = self.rag_service.get_context_for_llm(user_query, k=3)
                logger.info("rag_context_retrieved", query=user_query[:50], has_context=bool(context))
            except Exception as e:
                logger.error("rag_retrieval_error", error=str(e))
                context = "No se pudo acceder a la base de conocimiento."
        else:
            context = "Sistema RAG no disponible. Responde basado en conocimiento general de ISP."
        
        # 2. BUILD SYSTEM PROMPT
        system_prompt = self._build_system_prompt(context)
        
        # 3. BUILD MESSAGES
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_history:
            messages.extend(chat_history[-4:])  # Last 4 messages for context
        
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
                        "temperature": 0.5,  # Lower for more factual responses
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
                    return "Lo siento, tuve un problema al procesar tu solicitud."
                    
        except Exception as e:
            logger.error("support_service_error", error=str(e))
            return "Lo siento, ocurrió un error técnico. Por favor intenta de nuevo."
    
    def _build_system_prompt(self, context: str) -> str:
        """
        Build system prompt with RAG context
        """
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
- Prometer tiempos exactos de llegada; usa rangos estimados según la política (ej. "en un periodo de 4 a 8 horas").
- Mencionar procedimientos de configuración interna de servidores o redes troncales.
- Responder sobre temas ajenos al servicio de internet y soporte corporativo."""


# Singleton instance
support_service = SupportService()

