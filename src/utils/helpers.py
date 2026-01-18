"""
Utility helper functions
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
    """Check if business is currently open"""
    if now is None:
        now = datetime.now()
    
    day_name = now.strftime("%A").lower()
    working_hours = business_config.get("delivery", {}).get("working_hours", {})
    
    if day_name not in working_hours:
        return False
    
    hours = working_hours[day_name]
    open_time = datetime.strptime(hours["open"], "%H:%M").time()
    close_time = datetime.strptime(hours["close"], "%H:%M").time()
    current_time = now.time()
    
    return open_time <= current_time <= close_time


def get_business_hours_message() -> str:
    """Get formatted business hours message"""
    working_hours = business_config.get("delivery", {}).get("working_hours", {})
    
    if not working_hours:
        return "Consulta nuestros horarios de atención."
    
    days_map = {
        "monday": "Lunes",
        "tuesday": "Martes",
        "wednesday": "Miércoles",
        "thursday": "Jueves",
        "friday": "Viernes",
        "saturday": "Sábado",
        "sunday": "Domingo"
    }
    
    message = "📅 *Horarios de atención:*\n\n"
    for day, hours in working_hours.items():
        day_es = days_map.get(day, day.capitalize())
        message += f"{day_es}: {hours['open']} - {hours['close']}\n"
    
    return message


def calculate_delivery_fee(zone_name: Optional[str] = None) -> float:
    """Calculate delivery fee based on zone"""
    zones = business_config.get("delivery", {}).get("zones", [])
    
    if not zones:
        from .config import settings
        return settings.delivery_fee_base
    
    if zone_name:
        for zone in zones:
            if zone["name"].lower() == zone_name.lower():
                return zone["delivery_fee"]
    
    # Return first zone fee as default
    return zones[0]["delivery_fee"] if zones else 5.0


def generate_order_id() -> str:
    """Generate unique order ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_part = hashlib.md5(timestamp.encode()).hexdigest()[:6].upper()
    return f"ORD-{timestamp}-{hash_part}"


def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[<>{}]', '', text)
    return text


def extract_address_from_message(message: str) -> Optional[str]:
    """Extract address from user message"""
    message = sanitize_input(message)
    indicators = ['calle', 'avenida', 'av.', 'pasaje', 'jr.', 'mz.', 'lote', '#']
    message_lower = message.lower()
    
    for indicator in indicators:
        if indicator in message_lower:
            return message
    
    if len(message) > 10:
        return message
    
    return None


def format_menu_item(item: Dict[str, Any]) -> str:
    """Format menu item for display"""
    name = item.get("name", "")
    description = item.get("description", "")
    price = format_currency(item.get("price", 0))
    available = "✅" if item.get("available", False) else "❌"
    
    return f"{available} *{name}* - {price}\n   {description}"


def format_order_summary(order: Dict[str, Any]) -> str:
    """Format order summary for confirmation"""
    items = order.get("items", [])
    total = order.get("total", 0)
    delivery_fee = order.get("delivery_fee", 0)
    
    summary = "🛒 *Resumen de tu pedido:*\n\n"
    
    for item in items:
        name = item.get("name", "")
        quantity = item.get("quantity", 1)
        price = item.get("price", 0)
        subtotal = quantity * price
        summary += f"• {quantity}x {name} - {format_currency(subtotal)}\n"
    
    summary += f"\n💰 Subtotal: {format_currency(total)}"
    summary += f"\n🚚 Delivery: {format_currency(delivery_fee)}"
    summary += f"\n*Total: {format_currency(total + delivery_fee)}*"
    
    return summary
