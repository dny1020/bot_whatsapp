"""
Servicio de LLM (Groq) y NLP
"""

import re
import httpx

from ..settings import GROQ_API_KEY, GROQ_MODEL, business_config, flows_config, get_logger

logger = get_logger(__name__)

# Cargar patrones de intents
_intent_patterns = flows_config.get("intents", {}).get("patterns", {})

# System prompt configurable desde settings.json
_business_name = business_config.get("business", {}).get("name", "Soporte")
_default_prompt = (
    "Eres un Asistente Virtual. Responde de forma profesional y concisa.\n"
    "CONTEXTO:\n{context}\n"
    "REGLAS:\n- Responde SOLO basado en el contexto.\n- Sé breve y directo."
)
SYSTEM_PROMPT = (
    business_config
    .get("bot", {})
    .get("system_prompt", _default_prompt)
    .replace("{business_name}", _business_name)
)


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
