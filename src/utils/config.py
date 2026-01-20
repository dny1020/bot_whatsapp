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
    
    # WhatsApp Configuration
    whatsapp_verify_token: str = Field(default="", alias="WHATSAPP_VERIFY_TOKEN")
    whatsapp_access_token: str = Field(default="", alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_id: str = Field(default="", alias="WHATSAPP_PHONE_ID")
    whatsapp_business_id: str = Field(default="", alias="WHATSAPP_BUSINESS_ID")
    whatsapp_api_version: str = Field(default="v18.0", alias="WHATSAPP_API_VERSION")
    
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
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    
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
    
    # Delivery Configuration
    delivery_radius_km: float = Field(default=10.0, alias="DELIVERY_RADIUS_KM")
    max_delivery_time_minutes: int = Field(default=60, alias="MAX_DELIVERY_TIME_MINUTES")
    delivery_fee_base: float = Field(default=5.0, alias="DELIVERY_FEE_BASE")
    
    # Security
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    
    # Feature Flags
    enable_rag: bool = Field(default=True, alias="ENABLE_RAG")
    enable_voice_messages: bool = Field(default=False, alias="ENABLE_VOICE_MESSAGES")
    enable_image_processing: bool = Field(default=False, alias="ENABLE_IMAGE_PROCESSING")
    enable_location_tracking: bool = Field(default=False, alias="ENABLE_LOCATION_TRACKING")
    
    # Demo/Mock Mode
    enable_mock_whatsapp: bool = Field(default=False, alias="ENABLE_MOCK_WHATSAPP")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        populate_by_name = True


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
            "name": "Mi Negocio",
            "description": "Servicio de delivery",
        },
        "delivery": {"zones": [], "working_hours": {}},
        "menu": {"categories": []},
        "payment_methods": []
    }


# Load business config
business_config = load_business_config()
