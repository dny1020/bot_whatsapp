"""
LLM Service - Groq Integration
"""

import httpx
from typing import List, Dict

from ..settings import settings, get_logger
from .rag import rag_service

logger = get_logger(__name__)


class LLMService:
    """LLM service using Groq API with RAG context"""

    SYSTEM_PROMPT_TEMPLATE = """Eres el Asistente Virtual de soporte técnico para un ISP.
Responde de forma profesional, cortés y CONCISA (máximo 3-4 oraciones por respuesta).

CONTEXTO:
{context}

REGLAS:
- Responde SOLO basado en el contexto. Si no hay info, ofrece transferir a un agente.
- Usa español profesional y pasos numerados cuando sea necesario.
- SÉ BREVE: respuestas cortas y directas.
- NO menciones procedimientos internos ni prometas tiempos exactos."""

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    async def get_response(
        self, query: str, chat_history: List[Dict[str, str]] | None = None
    ) -> str:
        """Get LLM response with RAG context"""
        if not self.api_key:
            return "Lo siento, el servicio de IA no está configurado actualmente."

        # Retrieve context
        context = rag_service.get_context_for_llm(query, k=3)
        logger.info(
            "rag_context_retrieved", query=query[:50], has_context=bool(context)
        )

        # Build messages
        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(context=context)
        messages = [{"role": "system", "content": system_prompt}]

        if chat_history:
            messages.extend(chat_history[-4:])

        messages.append({"role": "user", "content": query})

        # Call LLM
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.5,
                        "max_tokens": 350,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    answer = data["choices"][0]["message"]["content"]
                    logger.info("llm_response_generated", query=query[:50])
                    return answer
                else:
                    logger.error("groq_api_error", status_code=response.status_code)
                    return "Lo siento, tuve un problema al procesar su solicitud."

        except Exception as e:
            logger.error("llm_service_error", error=str(e))
            return "Lo siento, ocurrió un error técnico. Por favor intente de nuevo."


llm_service = LLMService()
