"""
Configuration management for the application
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Twilio WhatsApp Configuration
    twilio_account_sid: str = Field(default="", alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(default="", alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(default="", alias="TWILIO_PHONE_NUMBER")
    
    # Application
    env: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    
    # Database
    database_url: str = Field(
        default="postgresql://chatbot:chatbot_password@localhost:5432/chatbot_db",
        alias="DATABASE_URL"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    webhook_port: int = Field(default=8001, alias="WEBHOOK_PORT")
    
    # NLP/LLM Configuration
    nlp_model_path: str = Field(default="models/base-model", alias="NLP_MODEL_PATH")
    use_local_model: bool = Field(default=False, alias="USE_LOCAL_MODEL")
    
    # LLM Providers
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: Optional[str] = Field(default="gpt-3.5-turbo", alias="OPENAI_MODEL")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: Optional[str] = Field(default="claude-3-haiku-20240307", alias="ANTHROPIC_MODEL")
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model: Optional[str] = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")
    
    # Embeddings
    use_local_embeddings: bool = Field(default=False, alias="USE_LOCAL_EMBEDDINGS")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    
    # NLP Features
    enable_intent_classification: bool = Field(default=True, alias="ENABLE_INTENT_CLASSIFICATION")
    enable_entity_extraction: bool = Field(default=True, alias="ENABLE_ENTITY_EXTRACTION")
    enable_sentiment_analysis: bool = Field(default=True, alias="ENABLE_SENTIMENT_ANALYSIS")
    enable_llm_fallback: bool = Field(default=False, alias="ENABLE_LLM_FALLBACK")
    
    # Delivery Configuration - REMOVED (ISP Support Mode)
    
    # Security
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    
    # Feature Flags
    enable_rag: bool = Field(default=True, alias="ENABLE_RAG")
    enable_voice_messages: bool = Field(default=False, alias="ENABLE_VOICE_MESSAGES")
    enable_image_processing: bool = Field(default=False, alias="ENABLE_IMAGE_PROCESSING")
    enable_location_tracking: bool = Field(default=False, alias="ENABLE_LOCATION_TRACKING")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        populate_by_name = True
        extra = 'allow'  # Permitir campos extras del .env


# Global settings instance
settings = Settings()


def load_business_config() -> Dict[str, Any]:
    """Load business configuration from settings.json"""
    config_path = Path(__file__).parent.parent.parent / "config" / "settings.json"
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return {
        "business": {
            "name": "ISP Support Bot",
            "description": "Asistente virtual de tu proveedor de internet",
        },
        "support": {
            "hours": "24/7", 
            "contact_phone": "+1234567890",
            "website": "www.tu-isp.com"
        },
        "plans": [
            {"name": "Básico", "speed": "100MB", "price": 20},
            {"name": "Pro", "speed": "300MB", "price": 35},
            {"name": "Gamer", "speed": "600MB", "price": 50}
        ]
    }


# Load business config
business_config = load_business_config()
