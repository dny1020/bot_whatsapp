"""
Unified WhatsApp Bot Application - Simplified Edition
"""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.settings import settings, setup_logging, get_logger
from src.db import init_db, get_db_context
from src.handlers import message_handler
from src.routes import router as api_router

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="ISP Support Bot",
    description="WhatsApp bot for ISP technical support",
    version="3.0.0",
)

origins = (
    settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1", tags=["API"])


@app.on_event("startup")
async def startup_event():
    logger.info("application_starting", env=settings.env)
    init_db()
    logger.info("application_ready")


@app.get("/")
async def root():
    return {"status": "running", "service": "isp-bot", "version": "3.0.0"}


@app.get("/health")
async def health():
    try:
        from sqlalchemy import text

        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "ok",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Unhealthy")


@app.post("/webhook/twilio")
async def twilio_webhook(request: Request):
    try:
        form_data = await request.form()
        from_phone = form_data.get("From", "").replace("whatsapp:", "")
        body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")

        logger.info("webhook_received", phone=from_phone, sid=message_sid)

        if body and from_phone:
            asyncio.create_task(
                message_handler.process_message(from_phone, body, message_sid)
            )

        return Response(content="", status_code=200)
    except Exception as e:
        logger.error("webhook_error", error=str(e))
        return Response(content="", status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.api_port)
