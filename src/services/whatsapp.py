"""
Servicio de WhatsApp (Twilio)
"""

import httpx
from base64 import b64encode

from ..settings import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, get_logger

logger = get_logger(__name__)

MAX_MESSAGE_LENGTH = 1600

# Configurar auth de Twilio
_base_url = ""
_headers = {}

if TWILIO_ACCOUNT_SID:
    _base_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}"
    auth_string = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
    _headers = {
        "Authorization": f"Basic {b64encode(auth_string.encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


async def send_message(to, message):
    """Enviar mensaje de texto por WhatsApp"""
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"
    
    # Limpiar mensaje
    message = "".join(c for c in message if c == '\n' or (ord(c) >= 32 and ord(c) != 127))
    
    # Truncar si es muy largo
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[:MAX_MESSAGE_LENGTH - 3] + "..."
    
    payload = {
        "From": TWILIO_PHONE_NUMBER,
        "To": to,
        "Body": message,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{_base_url}/Messages.json",
                data=payload,
                headers=_headers,
                timeout=30.0,
            )
            
            result = response.json()
            
            if response.status_code >= 400:
                logger.error(f"Error enviando mensaje: {result.get('message')}")
            
            return result
    except Exception as e:
        logger.error(f"Error en WhatsApp: {e}")
        return {"error": str(e)}


async def send_menu(to, body, buttons, header=None):
    """Enviar menu con opciones numeradas"""
    msg = ""
    if header:
        msg = f"*{header}*\n\n"
    msg += f"{body}\n\n"

    for i, btn in enumerate(buttons[:10], 1):
        title = btn.get("title", "")
        msg += f"*{i}.* {title}\n"

    msg += "\n_Responda con el numero de su opcion_"
    
    return await send_message(to, msg)
