"""
WhatsApp Cloud API client
"""
import httpx
from typing import Optional, Dict, Any, List
from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppClient:
    """Client for WhatsApp Cloud API"""
    
    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{settings.whatsapp_api_version}"
        self.phone_id = settings.whatsapp_phone_id
        self.access_token = settings.whatsapp_access_token
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def send_text_message(
        self, 
        to: str, 
        message: str, 
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """Send text message"""
        url = f"{self.base_url}/{self.phone_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": message
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                
                result = response.json()
                logger.info("message_sent", to=to, message_id=result.get("messages", [{}])[0].get("id"))
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
        """Send interactive button message (max 3 buttons)"""
        url = f"{self.base_url}/{self.phone_id}/messages"
        
        button_list = []
        for idx, btn in enumerate(buttons[:3]):  # Max 3 buttons
            button_list.append({
                "type": "reply",
                "reply": {
                    "id": btn.get("id", f"btn_{idx}"),
                    "title": btn.get("title", f"Option {idx+1}")[:20]  # Max 20 chars
                }
            })
        
        interactive = {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": button_list}
        }
        
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}
        
        if footer_text:
            interactive["footer"] = {"text": footer_text}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                
                result = response.json()
                logger.info("interactive_message_sent", to=to)
                return result
                
        except Exception as e:
            logger.error("send_interactive_error", to=to, error=str(e))
            raise
    
    async def send_interactive_list(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send interactive list message"""
        url = f"{self.base_url}/{self.phone_id}/messages"
        
        interactive = {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
        
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}
        
        if footer_text:
            interactive["footer"] = {"text": footer_text}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                
                result = response.json()
                logger.info("list_message_sent", to=to)
                return result
                
        except Exception as e:
            logger.error("send_list_error", to=to, error=str(e))
            raise
    
    async def send_image(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send image message"""
        url = f"{self.base_url}/{self.phone_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": {
                "link": image_url
            }
        }
        
        if caption:
            payload["image"]["caption"] = caption
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                
                result = response.json()
                logger.info("image_sent", to=to)
                return result
                
        except Exception as e:
            logger.error("send_image_error", to=to, error=str(e))
            raise
    
    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark message as read"""
        url = f"{self.base_url}/{self.phone_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("mark_read_error", message_id=message_id, error=str(e))
            return {}


# Global WhatsApp client instance
whatsapp_client = WhatsAppClient()
