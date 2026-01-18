"""
LLM Service - Handles AI model interactions
Supports both OpenAI API and local models
"""
from typing import Optional, Dict, Any, List
from enum import Enum
import httpx
from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    GROQ = "groq"


class LLMService:
    """Service for interacting with Language Models"""
    
    def __init__(self):
        self.provider = self._determine_provider()
        self.model_name = self._get_model_name()
        self.temperature = 0.7
        self.max_tokens = 500
        
        logger.info("llm_service_initialized", provider=self.provider.value, model=self.model_name)
    
    def _determine_provider(self) -> LLMProvider:
        """Determine which LLM provider to use"""
        if settings.use_local_model:
            return LLMProvider.LOCAL
        
        if settings.openai_api_key:
            return LLMProvider.OPENAI
        
        if settings.anthropic_api_key:
            return LLMProvider.ANTHROPIC
        
        if settings.groq_api_key:
            return LLMProvider.GROQ
        
        logger.warning("no_llm_configured", message="No LLM provider configured, using fallback")
        return LLMProvider.LOCAL
    
    def _get_model_name(self) -> str:
        """Get model name based on provider"""
        if self.provider == LLMProvider.OPENAI:
            return settings.openai_model or "gpt-3.5-turbo"
        elif self.provider == LLMProvider.ANTHROPIC:
            return settings.anthropic_model or "claude-3-haiku-20240307"
        elif self.provider == LLMProvider.GROQ:
            return settings.groq_model or "llama-3.1-8b-instant"
        else:
            return settings.nlp_model_path
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text response from LLM"""
        try:
            if self.provider == LLMProvider.OPENAI:
                return await self._generate_openai(prompt, system_prompt, temperature, max_tokens)
            elif self.provider == LLMProvider.ANTHROPIC:
                return await self._generate_anthropic(prompt, system_prompt, temperature, max_tokens)
            elif self.provider == LLMProvider.GROQ:
                return await self._generate_groq(prompt, system_prompt, temperature, max_tokens)
            else:
                return await self._generate_local(prompt, system_prompt)
        except Exception as e:
            logger.error("llm_generation_error", error=str(e), provider=self.provider.value)
            return "Lo siento, hubo un error procesando tu solicitud."
    
    async def _generate_openai(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> str:
        """Generate response using OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.info("openai_response_generated", tokens=result.get("usage", {}).get("total_tokens"))
            return content.strip()
    
    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> str:
        """Generate response using Anthropic Claude API"""
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if temperature:
            payload["temperature"] = temperature
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            result = response.json()
            content = result["content"][0]["text"]
            
            logger.info("anthropic_response_generated")
            return content.strip()
    
    async def _generate_groq(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> str:
        """Generate response using Groq API"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.info("groq_response_generated")
            return content.strip()
    
    async def _generate_local(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Generate response using local model (fallback)"""
        logger.warning("local_model_not_implemented")
        return "Función de modelo local no implementada. Por favor configura un proveedor LLM."
    
    async def extract_intent(self, message: str) -> str:
        """Extract user intent from message"""
        system_prompt = """Eres un clasificador de intenciones para un chatbot de delivery.
Clasifica el mensaje del usuario en una de estas categorías:
- greeting (saludos)
- show_menu (ver menú)
- order (hacer pedido)
- track_order (rastrear pedido)
- hours (horarios)
- help (ayuda)
- cancel (cancelar)
- other (otro)

Responde SOLO con el nombre de la categoría."""

        intent = await self.generate_response(
            prompt=f"Mensaje: {message}",
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=10
        )
        
        return intent.lower().strip()
    
    async def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from message (address, phone, name, etc.)"""
        system_prompt = """Extrae entidades del mensaje del usuario.
Responde en formato JSON con estas claves (deja vacío si no existe):
- address: dirección de entrega
- phone: número de teléfono
- name: nombre de la persona
- product: producto mencionado
- quantity: cantidad

Ejemplo: {"address": "Calle 123", "phone": "", "name": "Juan", "product": "pizza", "quantity": "2"}"""

        entities_json = await self.generate_response(
            prompt=f"Mensaje: {message}",
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=150
        )
        
        try:
            import json
            entities = json.loads(entities_json)
            return entities
        except Exception as e:
            logger.error("entity_extraction_error", error=str(e))
            return {}
    
    async def generate_friendly_response(
        self,
        context: str,
        user_message: str,
        intent: str
    ) -> str:
        """Generate a friendly, contextual response"""
        system_prompt = f"""Eres un asistente amigable de un servicio de delivery.
Contexto actual: {context}
Intención del usuario: {intent}

Genera una respuesta natural, breve y útil en español.
Mantén un tono amigable y profesional."""

        response = await self.generate_response(
            prompt=user_message,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=200
        )
        
        return response


# Global LLM service instance
llm_service = LLMService()
