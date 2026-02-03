"""
Utility Functions
"""

import re
import hashlib
from datetime import datetime


def normalize_phone(phone: str) -> str:
    """Normalize phone number format (digits only)"""
    return re.sub(r"\D", "", phone)


def validate_phone(phone: str) -> bool:
    """Validate phone number has at least 10 digits"""
    return len(normalize_phone(phone)) >= 10


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:.2f}"


def generate_ticket_id() -> str:
    """Generate unique ticket ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_part = hashlib.md5(timestamp.encode()).hexdigest()[:6].upper()
    return f"TICKET-{timestamp}-{hash_part}"


def sanitize_input(text: str) -> str:
    """Sanitize user input: normalize whitespace, remove dangerous chars"""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[<>{}]", "", text)
    return text
