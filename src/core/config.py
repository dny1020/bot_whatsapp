"""
Core Configuration, Logging, and Utilities
Consolidated from src/utils/
"""
import os
import re
import json
import logging
import hashlib
import structlog
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple
from pydantic_settings import BaseSettings
from pydantic import Field

# ============================================================================
# SETTINGS
# ============================================================================

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
    
    # LLM Providers
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_model: Optional[str] = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    
    # Feature Flags
    enable_rag: bool = Field(default=True, alias="ENABLE_RAG")
    
    # Security
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        populate_by_name = True
        extra = 'allow'

settings = Settings()

# ============================================================================
# BUSINESS CONFIG
# ============================================================================

def load_business_config() -> Dict[str, Any]:
    """Load business configuration from settings.json"""
    # Adjust path for new core location
    config_path = Path(__file__).parent.parent.parent / "config" / "settings.json"
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return {
        "business": {
            "name": "ISP Support Bot",
            "description": "Asistente virtual de su proveedor de internet",
        },
        "support": {
            "hours": "24/7", 
            "contact_phone": "+1234567890",
            "website": "www.tu-isp.com"
        }
    }

business_config = load_business_config()

# ============================================================================
# LOGGING
# ============================================================================

def setup_logging():
    """Configure structured logging"""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(message)s",
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler()
        ]
    )
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
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

# ============================================================================
# UTILITIES
# ============================================================================

def normalize_phone(phone: str) -> str:
    """Normalize phone number format"""
    return re.sub(r'\D', '', phone)

def validate_phone(phone: str) -> bool:
    """Validate phone number"""
    normalized = normalize_phone(phone)
    return len(normalized) >= 10

def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:.2f}"

def is_business_open() -> bool:
    """Check if business is open (ISP defaults to 24/7)"""
    return True

def get_business_hours_message() -> str:
    """Get formatted business hours message"""
    support = business_config.get("support", {})
    hours = support.get("hours", "24/7")
    return f"Horario de atención: {hours}"

def generate_ticket_id() -> str:
    """Generate unique ticket ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_part = hashlib.md5(timestamp.encode()).hexdigest()[:6].upper()
    return f"TICKET-{timestamp}-{hash_part}"

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[<>{}]', '', text)
    return text
