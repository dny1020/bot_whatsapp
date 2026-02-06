"""
Servicio de LLM (Groq) y NLP
"""

import re
import httpx

from ..settings import GROQ_API_KEY, GROQ_MODEL, flows_config, get_logger

logger = get_logger(__name__)

# Cargar patrones de intents
_intent_patterns = flows_config.get("intents", {}).get("patterns", {})

SYSTEM_PROMPT = """Eres el Asistente Virtual de soporte técnico para un ISP.
Responde de forma profesional, cortés y CONCISA (máximo 3-4 oraciones por respuesta).

CONTEXTO:
{context}

REGLAS:
- Responde SOLO basado en el contexto. Si no hay info, ofrece transferir a un agente.
- Usa español profesional y pasos numerados cuando sea necesario.
- SÉ BREVE: respuestas cortas y directas.
- NO menciones procedimientos internos ni prometas tiempos exactos."""


def classify_intent(message):
    """Clasificar intención del mensaje usando patrones regex"""
    msg = message.lower().strip()

    for intent, patterns in _intent_patterns.items():
        for pattern in patterns:
            if re.search(pattern, msg):
                return intent

    return "unknown"


async def get_llm_response(query, chat_history=None):
    """Obtener respuesta del LLM con contexto RAG"""
    if not GROQ_API_KEY:
        return "Lo siento, el servicio de IA no está configurado."

    # Importar RAG aquí para evitar import circular
    from .rag import get_context_for_query
    
    # Obtener contexto
    context = get_context_for_query(query)
    
    # Construir mensajes
    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        messages.extend(chat_history[-4:])

    messages.append({"role": "user", "content": query})

    # Llamar a Groq
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "temperature": 0.5,
                    "max_tokens": 350,
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"Error de Groq API: {response.status_code}")
                return "Lo siento, tuve un problema al procesar su solicitud."

    except Exception as e:
        logger.error(f"Error en LLM: {e}")
        return "Lo siento, ocurrió un error técnico. Por favor intente de nuevo."
