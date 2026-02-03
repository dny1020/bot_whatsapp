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

    SYSTEM_PROMPT_TEMPLATE = """Eres el Asistente Virtual Especializado de soporte técnico para un Proveedor de Internet (ISP).
Tu objetivo es brindar asistencia técnica profesional, cortés y eficiente.

CONTEXTO DE LA BASE DE CONOCIMIENTO:
{context}

REGLAS DE TONO Y PROFESIONALISMO:
1. 🤵 **Trato Formal**: Dirígete siempre al cliente. Mantén un tono corporativo y respetuoso en todo momento.
2. 🛡️ **Privacidad de Información**: NO uses códigos internos, etiquetas de categorías técnicas o términos de manual interno.
3. 📝 **Claridad**: Traduce la información técnica a un lenguaje que el cliente entienda, sin perder la precisión.
4. 🏢 **Identidad**: Habla en nombre de la empresa ("En nuestra empresa...", "Nuestro equipo técnico...").

INSTRUCCIONES CRÍTICAS:
1. 🎯 **Fidelidad**: Responde ÚNICAMENTE basado en el contexto proporcionado.
2. ❌ **No Inventar**: Si algo no está en el contexto, indica amablemente que transferirás la consulta a un agente humano.
3. 🇪🇸 **Idioma**: Responde siempre en español profesional.
4. 🔧 **Soluciones**: Proporciona pasos de solución claros y numerados cuando sea pertinente.

PROHIBIDO:
- Usar lenguaje coloquial.
- Prometer tiempos exactos de llegada; usa rangos estimados según la política.
- Mencionar procedimientos de configuración interna de servidores o redes troncales."""

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
                        "max_tokens": 512,
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
