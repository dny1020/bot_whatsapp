import json
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SupportService:
    """Service to handle ISP technical support using Groq and local Knowledge Base"""
    
    def __init__(self):
        self.kb_path = Path(__file__).parent.parent.parent / "config" / "knowledge_base.json"
        self.kb_data = self._load_kb()
        self.groq_api_key = settings.groq_api_key
        self.groq_model = settings.groq_model or "llama-3.3-70b-versatile"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def _load_kb(self) -> List[Dict[str, Any]]:
        """Load the local knowledge base"""
        try:
            if self.kb_path.exists():
                with open(self.kb_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error("kb_load_error", error=str(e))
            return []

    def search_kb(self, query: str) -> str:
        """Simple keyword-based search in the local KB"""
        query_lower = query.lower()
        relevant_content = []
        
        for item in self.kb_data:
            content = item.get("content", "").lower()
            keywords = item.get("metadata", {}).get("keywords", [])
            
            # Check if any keyword matches or if query is in content
            if any(kw.lower() in query_lower for kw in keywords) or query_lower in content:
                relevant_content.append(item.get("content"))
        
        return "\n\n".join(relevant_content) if relevant_content else "No se encontró información específica en la base de conocimientos."

    async def get_ai_response(self, user_query: str, chat_history: List[Dict[str, str]] = None) -> str:
        """Process query using Groq with KB context"""
        if not self.groq_api_key:
            return "Lo siento, el servicio de IA no está configurado actualmente (falta API Key)."

        kb_context = self.search_kb(user_query)
        
        system_prompt = (
            "Eres el asistente virtual de soporte técnico de un proveedor de internet (ISP). "
            "Tu objetivo es ayudar a los clientes con problemas técnicos, dudas sobre facturación o planes. "
            "Utiliza la siguiente información de nuestra base de conocimientos si es relevante:\n\n"
            f"{kb_context}\n\n"
            "Instrucciones:\n"
            "- Sé amable y profesional.\n"
            "- Si el cliente tiene problemas de conexión, guíalo paso a paso.\n"
            "- Si no sabes la respuesta o es un problema complejo, sugiere contactar a un operador humano.\n"
            "- Responde siempre en español."
        )

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if chat_history:
            messages.extend(chat_history)
        
        messages.append({"role": "user", "content": user_query})

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
                        "temperature": 0.7,
                        "max_tokens": 512
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error("groq_api_error", status_code=response.status_code, text=response.text)
                    return "Lo siento, tuve un problema al procesar tu solicitud con el motor de IA."
                    
        except Exception as e:
            logger.error("support_service_error", error=str(e))
            return "Lo siento, ocurrió un error técnico al intentar procesar tu consulta."

# Singleton instance
support_service = SupportService()
