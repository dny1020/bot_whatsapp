"""
WhatsApp Webhook endpoint
"""
from fastapi import FastAPI, Request, Response, HTTPException, status
from typing import Dict, Any
import sys
sys.path.append('/home/debian/project/src')

from backend.message_processor import message_processor
from utils.config import settings
from utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="WhatsApp Webhook", version="1.0.0")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "ok", "service": "whatsapp-webhook"}


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.get("/webhook")
async def webhook_verification(request: Request):
    """
    Webhook verification endpoint for WhatsApp Cloud API
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    logger.info("webhook_verification_attempt", mode=mode)
    
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        logger.info("webhook_verified")
        return Response(content=challenge, media_type="text/plain")
    
    logger.warning("webhook_verification_failed", token_match=(token == settings.whatsapp_verify_token))
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")


@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Handle incoming webhook events from WhatsApp
    """
    try:
        body = await request.json()
        logger.debug("webhook_received", body=body)
        
        # Process webhook payload
        entry = body.get("entry", [])
        
        for item in entry:
            changes = item.get("changes", [])
            
            for change in changes:
                value = change.get("value", {})
                
                # Process messages
                messages = value.get("messages", [])
                
                for message in messages:
                    message_type = message.get("type")
                    from_phone = message.get("from")
                    message_id = message.get("id")
                    
                    logger.info(
                        "message_received",
                        from_phone=from_phone,
                        message_type=message_type,
                        message_id=message_id
                    )
                    
                    # Handle text messages
                    if message_type == "text":
                        text_content = message.get("text", {}).get("body", "")
                        await message_processor.process_message(from_phone, text_content, message_id)
                    
                    # Handle interactive responses (button/list replies)
                    elif message_type == "interactive":
                        interactive = message.get("interactive", {})
                        
                        if interactive.get("type") == "button_reply":
                            button_id = interactive.get("button_reply", {}).get("id", "")
                            # Map button IDs to commands
                            button_commands = {
                                "btn_menu": "menu",
                                "btn_order": "pedido",
                                "btn_help": "ayuda"
                            }
                            command_text = button_commands.get(button_id, button_id)
                            await message_processor.process_message(from_phone, command_text, message_id)
                        
                        elif interactive.get("type") == "list_reply":
                            list_id = interactive.get("list_reply", {}).get("id", "")
                            await message_processor.process_message(from_phone, list_id, message_id)
                    
                    # Handle other message types
                    else:
                        logger.info("unsupported_message_type", message_type=message_type)
                        # Could handle images, documents, location, etc. here
                
                # Process status updates
                statuses = value.get("statuses", [])
                for status_update in statuses:
                    logger.debug("status_update", status=status_update)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error("webhook_error", error=str(e))
        # Return 200 to avoid WhatsApp retries
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.webhook_port,
        log_level=settings.log_level.lower()
    )
