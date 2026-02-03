"""
WhatsApp Client Service (Twilio)
"""

import httpx
from base64 import b64encode
from typing import Dict, Any, List

from ..settings import settings


class WhatsAppClient:
    """Twilio WhatsApp integration"""

    def __init__(self):
        self.base_url = ""
        self.headers = {}

        if settings.twilio_account_sid:
            self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}"
            auth_string = f"{settings.twilio_account_sid}:{settings.twilio_auth_token}"
            self.headers = {
                "Authorization": f"Basic {b64encode(auth_string.encode()).decode()}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

    async def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send text message via WhatsApp"""
        to_number = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        payload = {
            "From": settings.twilio_phone_number,
            "To": to_number,
            "Body": message,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/Messages.json",
                data=payload,
                headers=self.headers,
                timeout=30.0,
            )
            return response.json()

    async def send_interactive_buttons(
        self,
        to: str,
        body: str,
        buttons: List[Dict[str, str]],
        header: str | None = None,
    ) -> Dict[str, Any]:
        """Send interactive buttons (fallback to numbered text)"""
        msg = f"*{header}*\n\n" if header else ""
        msg += f"{body}\n\n"

        for idx, btn in enumerate(buttons[:10], 1):
            msg += f"{idx}. {btn.get('title')}\n"

        msg += "\nResponda con el número de su opción."
        return await self.send_text_message(to, msg)


whatsapp_client = WhatsAppClient()
