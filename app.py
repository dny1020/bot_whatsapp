"""
WhatsApp Bot - Aplicación principal
"""

import asyncio
from datetime import datetime

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.settings import ENV, API_PORT, get_logger
from src.db import init_db, get_db_session
from src.handlers import process_message
from src.routes import router as api_router

logger = get_logger(__name__)

# Crear app
app = FastAPI(
    title="WhatsApp Bot",
    description="Bot de WhatsApp para soporte ISP",
    version="3.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas API
app.include_router(api_router, prefix="/api/v1", tags=["API"])


@app.on_event("startup")
async def startup():
    """Inicializar aplicación"""
    logger.info(f"Iniciando aplicación en modo {ENV}")
    init_db()
    logger.info("Aplicación lista")


@app.get("/")
async def root():
    """Ruta principal"""
    return {"status": "running", "service": "whatsapp-bot", "version": "3.0.0"}


@app.get("/health")
async def health():
    """Health check"""
    try:
        from sqlalchemy import text
        db = get_db_session()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "database": "ok",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Health check falló: {e}")
        raise HTTPException(status_code=503, detail="Unhealthy")


@app.post("/webhook/twilio")
async def twilio_webhook(request: Request):
    """Webhook para recibir mensajes de Twilio"""
    try:
        form_data = await request.form()
        
        phone = form_data.get("From", "").replace("whatsapp:", "")
        body = form_data.get("Body", "")
        message_sid = form_data.get("MessageSid", "")

        logger.info(f"Mensaje recibido de {phone}: {body[:50]}...")

        if body and phone:
            # Procesar mensaje en background
            asyncio.create_task(process_message(phone, body, message_sid))

        return Response(content="", status_code=200)
    
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return Response(content="", status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
