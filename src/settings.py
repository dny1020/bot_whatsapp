"""
Configuración de la aplicación
"""

import os
import re
import json
import logging
import hashlib
from datetime import datetime

# Cargar variables de entorno desde .env si existe
from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# Configuración
# =============================================================================

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# App
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/chatbot.db")

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


# =============================================================================
# Logging simple
# =============================================================================

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def get_logger(name):
    """Obtener logger"""
    return logging.getLogger(name)


# =============================================================================
# Cargar configuración JSON
# =============================================================================

def load_json_config(filename, default):
    """Cargar archivo JSON de configuración"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", filename)
    
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Remover comentarios estilo /* */ y //
            import re
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            return json.loads(content)
    return default


business_config = load_json_config("settings.json", {
    "business": {"name": "ISP Support Bot", "description": "Asistente virtual"},
    "support": {"hours": "24/7", "contact_phone": "+1234567890"},
})

flows_config = load_json_config("flows.json", {
    "intents": {"allowed": [], "patterns": {}},
    "flows": {},
    "defaults": {}
})


# =============================================================================
# Funciones utilitarias
# =============================================================================

def normalize_phone(phone):
    """Normalizar número de teléfono (solo dígitos)"""
    return re.sub(r"\D", "", phone)


def validate_phone(phone):
    """Validar que el teléfono tenga al menos 10 dígitos"""
    return len(normalize_phone(phone)) >= 10


def format_currency(amount):
    """Formatear cantidad como moneda"""
    return f"${amount:.2f}"


def generate_ticket_id():
    """Generar ID único de ticket"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_part = hashlib.md5(timestamp.encode()).hexdigest()[:6].upper()
    return f"TICKET-{timestamp}-{hash_part}"


def sanitize_input(text):
    """Limpiar input del usuario"""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[<>{}]", "", text)
    return text
