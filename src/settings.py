"""
Application Settings and Configuration Loaders
"""

import json
import logging
import structlog
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Twilio WhatsApp
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
        alias="DATABASE_URL",
    )

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    # LLM
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # Features
    enable_rag: bool = Field(default=True, alias="ENABLE_RAG")

    # Security
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = False
        populate_by_name = True
        extra = "allow"


settings = Settings()


def _get_config_path(filename: str) -> Path:
    """Get path to config file"""
    return Path(__file__).parent.parent / "config" / filename


def load_json_config(filename: str, default: Dict[str, Any]) -> Dict[str, Any]:
    """Load JSON configuration file with fallback"""
    config_path = _get_config_path(filename)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


business_config = load_json_config(
    "settings.json",
    {
        "business": {"name": "ISP Support Bot", "description": "Asistente virtual"},
        "support": {"hours": "24/7", "contact_phone": "+1234567890"},
    },
)

flows_config = load_json_config(
    "flows.json",
    {"intents": {"allowed": [], "patterns": {}}, "flows": {}, "defaults": {}},
)


def setup_logging() -> None:
    """Configure structured logging"""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Get a structured logger"""
    return structlog.get_logger(name)
