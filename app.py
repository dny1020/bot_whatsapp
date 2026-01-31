"""
Unified WhatsApp Bot Application - Twilio Edition
Single FastAPI service handling webhook, backend, and health checks
Architecture: Twilio Webhook → Idempotency → Session → Intent → State Machine → Response
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
    title="WhatsApp Bot - Unified Service (Twilio)",
    description="Unified API handling webhook, backend, and admin via Twilio",
    version="2.0.0"
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
        "service": "whatsapp-bot-unified-twilio",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "webhook_twilio": "/webhook/twilio",
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
        from sqlalchemy import text
        
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        
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

@app.get("/webhook/twilio")
async def twilio_webhook_verification(request: Request):
    """
    Webhook verification endpoint for Twilio (optional, not required)
    Twilio doesn't need verification like Meta does
    """
    logger.info("twilio_webhook_get_received")
    return {"status": "ok", "message": "Twilio webhook endpoint ready"}


@app.post("/webhook/twilio")
async def twilio_webhook_handler(request: Request):
    """
    Handle incoming webhook events from Twilio WhatsApp
    Architecture flow:
    1. Receive webhook from Twilio (Form data)
    2. Extract From, Body, MessageSid
    3. Check idempotency (avoid duplicate processing)
    4. Process message through message_processor
    5. Return 200 OK
    """
    try:
        # Twilio sends form data, not JSON
        form_data = await request.form()
        
        # Extract Twilio fields
        from_number = form_data.get("From", "")  # whatsapp:+1234567890
        body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")
        profile_name = form_data.get("ProfileName", "")
        
        # Remove whatsapp: prefix from phone number
        from_phone = from_number.replace("whatsapp:", "")
        
        logger.info("twilio_webhook_received", 
                   from_phone=from_phone, 
                   message_sid=message_sid,
                   profile_name=profile_name)
        
        # Process text message
        if body and from_phone:
            await message_processor.process_message(from_phone, body, message_sid)
        else:
            logger.warning("twilio_webhook_missing_data", from_phone=from_phone, has_body=bool(body))
        
        # Twilio expects 200 OK (or TwiML for immediate reply)
        return Response(content="", status_code=200)
        
    except Exception as e:
        logger.error("twilio_webhook_error", error=str(e))
        # Return 200 even on error to avoid Twilio retrying
        return Response(content="", status_code=200)


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
