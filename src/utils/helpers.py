"""
Utility helper functions for ISP Support Bot
"""
import re
import hashlib
from datetime import datetime, time
from typing import Optional, Dict, Any
from .config import business_config


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


def is_business_open(now: Optional[datetime] = None) -> bool:
    """
    Check if business is currently open
    For ISP Support, we might default to True (24/7 automated) 
    or check specific hours if defined.
    """
    if now is None:
        now = datetime.now()
    
    # In this ISP context, let's assume the bot answers 24/7.
    # If human support has hours, that should be checked separately.
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


def extract_address_from_message(message: str) -> Optional[str]:
    """Extract address from user message (useful for technical visits)"""
    message = sanitize_input(message)
    indicators = ['calle', 'avenida', 'av.', 'pasaje', 'jr.', 'mz.', 'lote', '#']
    message_lower = message.lower()
    
    for indicator in indicators:
        if indicator in message_lower:
            return message
    
    return None
