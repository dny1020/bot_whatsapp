"""
Twilio WhatsApp API client
"""
import httpx
from typing import Optional, Dict, Any, List
from base64 import b64encode
from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppClient:
    """Client for Twilio WhatsApp API"""
    
    def __init__(self):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.from_number = settings.twilio_phone_number
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
        
        # Basic Auth
        auth_string = f"{self.account_sid}:{self.auth_token}"
        self.auth_header = b64encode(auth_string.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {self.auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    async def send_text_message(
        self, 
        to: str, 
        message: str, 
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """Send text message via Twilio"""
        url = f"{self.base_url}/Messages.json"
        
        # Ensure phone number has whatsapp: prefix
        to_number = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        
        payload = {
            "From": self.from_number,
            "To": to_number,
            "Body": message
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=payload, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                
                result = response.json()
                logger.info("message_sent", to=to, message_sid=result.get("sid"))
                return result
                
        except Exception as e:
            logger.error("send_message_error", to=to, error=str(e))
            raise
    
    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send interactive button message
        NOTE: Twilio requires pre-approved templates for buttons
        Fallback to numbered text message
        """
        logger.warning("interactive_buttons_fallback", 
                      message="Twilio requires approved templates. Sending as text with options.")
        
        # Build text with numbered options
        full_message = ""
        if header_text:
            full_message += f"*{header_text}*\n\n"
        
        full_message += f"{body_text}\n\n"
        
        for idx, btn in enumerate(buttons[:10], 1):
            title = btn.get("title", f"Opción {idx}")
            full_message += f"{idx}. {title}\n"
        
        if footer_text:
            full_message += f"\n_{footer_text}_"
        
        full_message += "\n\nResponde con el número de tu opción."
        
        return await self.send_text_message(to, full_message)
    
    async def send_interactive_list(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send interactive list message
        NOTE: Twilio requires pre-approved templates
        Fallback to text with numbered sections
        """
        logger.warning("interactive_list_fallback",
                      message="Twilio requires approved templates. Sending as text.")
        
        full_message = ""
        if header_text:
            full_message += f"*{header_text}*\n\n"
        
        full_message += f"{body_text}\n\n"
        
        option_num = 1
        for section in sections:
            section_title = section.get("title", "")
            if section_title:
                full_message += f"*{section_title}*\n"
            
            rows = section.get("rows", [])
            for row in rows:
                title = row.get("title", f"Opción {option_num}")
                description = row.get("description", "")
                full_message += f"{option_num}. {title}"
                if description:
                    full_message += f" - {description}"
                full_message += "\n"
                option_num += 1
            
            full_message += "\n"
        
        if footer_text:
            full_message += f"_{footer_text}_\n\n"
        
        full_message += "Responde con el número de tu opción."
        
        return await self.send_text_message(to, full_message)
    
    async def send_image(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send image message via Twilio"""
        url = f"{self.base_url}/Messages.json"
        
        to_number = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        
        payload = {
            "From": self.from_number,
            "To": to_number,
            "MediaUrl": image_url
        }
        
        if caption:
            payload["Body"] = caption
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=payload, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                
                result = response.json()
                logger.info("image_sent", to=to, message_sid=result.get("sid"))
                return result
                
        except Exception as e:
            logger.error("send_image_error", to=to, error=str(e))
            raise
    
    async def mark_as_read(self, message_sid: str) -> Dict[str, Any]:
        """
        Mark message as read
        NOTE: Twilio doesn't support read receipts via API
        """
        logger.debug("mark_as_read_not_supported", 
                    message="Twilio doesn't support read receipts")
        return {"status": "not_supported"}


# Global WhatsApp client instance
whatsapp_client = WhatsAppClient()
