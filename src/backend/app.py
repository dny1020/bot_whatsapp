"""
Main backend application
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import sys
sys.path.append('/home/debian/project/src')

from backend.database import get_db, init_db
from backend.models import User
from backend.routes import router
from utils.config import settings, business_config
from utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="WhatsApp Chatbot Backend",
    description="Backend API for WhatsApp Support ISP Chatbot",
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

# Include routes
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("application_starting", env=settings.env)
    
    try:
        # Initialize database
        init_db()
        logger.info("database_initialized")
        
        logger.info("application_ready")
    except Exception as e:
        logger.error("startup_error", error=str(e))
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "whatsapp-chatbot-backend",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.env
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
