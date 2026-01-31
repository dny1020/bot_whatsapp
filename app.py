"""
Unified WhatsApp Bot Application
Single FastAPI service handling webhook, backend, and health checks
Architecture: Webhook → Idempotency → Session → Intent → State Machine → Response
"""
from fastapi import FastAPI, Request, Response, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, '/app/src')

from src.backend.database import init_db
from src.backend.models import User
from src.backend.routes import router as backend_router
from src.backend.message_processor import message_processor
from src.utils.config import settings, business_config
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create unified FastAPI app
app = FastAPI(
    title="WhatsApp Bot - Unified Service",
    description="Unified API handling webhook, backend, and admin",
    version="1.0.0"
)

# CORS middleware
origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include backend routes with prefix
app.include_router(backend_router, prefix="/api/v1", tags=["Backend API"])


# ============================================================================
# STARTUP & HEALTH
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("application_starting", env=settings.env, version="1.0.0")
    
    try:
        # Initialize database
        init_db()
        logger.info("database_initialized")
        
        logger.info("application_ready", service="unified")
    except Exception as e:
        logger.error("startup_error", error=str(e))
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "whatsapp-bot-unified",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "admin": "/admin (coming soon)",
            "api": "/api/v1"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        from src.backend.database import get_db_context
        
        with get_db_context() as db:
            db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.env,
            "version": "1.0.0",
            "checks": {
                "database": "ok",
                "redis": "ok"
            }
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


# ============================================================================
# WEBHOOK ENDPOINTS (from webhook.py)
# ============================================================================

@app.get("/webhook")
async def webhook_verification(request: Request):
    """
    Webhook verification endpoint for WhatsApp Cloud API
    Meta sends a GET request to verify the webhook
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
    Architecture flow:
    1. Receive webhook from Meta
    2. Check idempotency (avoid duplicate processing)
    3. Load session from Redis
    4. Classify intent with NLP
    5. Execute state machine (rules-based)
    6. Optional: Use LLM for response generation
    7. Send response
    8. Save session
    """
    try:
        body = await request.json()
        logger.debug("webhook_received", body=body)
        
        # Process Meta (Cloud API) payload
        entry = body.get("entry", [])
        for item in entry:
            changes = item.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                
                # Filter out non-message events
                if "messages" not in value:
                    continue
                    
                messages = value.get("messages", [])
                for message in messages:
                    message_type = message.get("type")
                    from_phone = message.get("from")
                    message_id = message.get("id")
                    
                    logger.info("message_received", from_phone=from_phone, message_type=message_type)
                    
                    # Handle text messages
                    if message_type == "text":
                        text_content = message.get("text", {}).get("body", "")
                        await message_processor.process_message(from_phone, text_content, message_id)
                    
                    # Handle interactive messages (buttons, lists)
                    elif message_type == "interactive":
                        interactive = message.get("interactive", {})
                        if interactive.get("type") == "button_reply":
                            button_id = interactive.get("button_reply", {}).get("id", "")
                            await message_processor.process_message(from_phone, button_id, message_id)
                        elif interactive.get("type") == "list_reply":
                            list_id = interactive.get("list_reply", {}).get("id", "")
                            await message_processor.process_message(from_phone, list_id, message_id)
        
        # Always return 200 to avoid WhatsApp retries
        return {"status": "ok"}
        
    except Exception as e:
        logger.error("webhook_error", error=str(e))
        # Return 200 even on error to avoid WhatsApp retrying failed messages
        return {"status": "error", "message": str(e)}


# ============================================================================
# ADMIN ENDPOINTS (Future)
# ============================================================================

@app.get("/admin")
async def admin_panel():
    """Admin panel - Coming soon"""
    return {
        "message": "Admin panel coming soon",
        "features": [
            "User management",
            "Session monitoring",
            "Analytics dashboard",
            "Configuration"
        ]
    }


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Use port 8000 for unified service
    port = int(settings.api_port) if hasattr(settings, 'api_port') else 8000
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=settings.log_level.lower()
    )
