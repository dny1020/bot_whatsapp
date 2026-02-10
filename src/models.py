"""
Modelos de base de datos y esquemas de respuesta
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, relationship
from pydantic import BaseModel


class Base(DeclarativeBase):
    """Base para todos los modelos SQLAlchemy"""
    pass


# =============================================================================
# Esquemas Pydantic (para respuestas API)
# =============================================================================

class SupportTicketResponse(BaseModel):
    ticket_id: str
    issue_type: str
    status: str
    priority: str
    subject: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    phone: str
    name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TicketStats(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    avg_resolution_time_hours: float


class MessageAnalytics(BaseModel):
    period_days: int
    total_messages: int
    inbound_messages: int
    outbound_messages: int


# =============================================================================
# Modelos SQLAlchemy
# =============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100))
    email = Column(String(100))
    
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    total_conversations = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")
    support_tickets = relationship("SupportTicket", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(100), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone = Column(String(20), index=True, nullable=False)
    
    status = Column(String(20), default="active", index=True)
    state = Column(String(50), default="idle")
    context = Column(MutableDict.as_mutable(JSON), default={})
    
    message_count = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ttl_expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(100), primary_key=True)
    conversation_id = Column(String(100), ForeignKey("conversations.id"), nullable=False)
    
    sender = Column(String(20))  # 'user' o 'bot'
    direction = Column(String(10))  # 'inbound' o 'outbound'
    message_type = Column(String(20))
    content = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    issue_type = Column(String(50))
    priority = Column(String(20), default="medium")
    subject = Column(String(200))
    description = Column(Text)
    status = Column(String(20), default="open")
    
    resolution = Column(Text)
    resolved_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="support_tickets")
