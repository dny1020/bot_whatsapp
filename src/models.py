"""
SQLAlchemy Database Models
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Enum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ConversationStatus(str, enum.Enum):
    active = "active"
    idle = "idle"
    closed = "closed"
    archived = "archived"


class User(Base):
    """User/Customer model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100))
    nickname = Column(String(100))
    email = Column(String(100))

    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    total_conversations = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    language = Column(String(10), default="es")
    preferences = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")
    support_tickets = relationship("SupportTicket", back_populates="user")


class Conversation(Base):
    """Chat conversation model"""

    __tablename__ = "conversations"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone = Column(String(20), index=True, nullable=False)

    status = Column(
        Enum(ConversationStatus), default=ConversationStatus.active, index=True
    )
    state = Column(String(50), default="idle")
    context = Column(JSON, default={})

    message_count = Column(Integer, default=0)
    topic = Column(String(200))

    last_activity = Column(DateTime, default=datetime.utcnow)
    ttl_expires_at = Column(DateTime)
    closed_at = Column(DateTime)
    close_reason = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Message log"""

    __tablename__ = "messages"

    id = Column(String(100), primary_key=True, index=True)
    conversation_id = Column(
        String(100), ForeignKey("conversations.id"), nullable=False
    )

    sender = Column(String(20))  # 'user' or 'bot'
    direction = Column(String(10))  # inbound, outbound
    message_type = Column(String(20))
    content = Column(Text)

    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)

    meta_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class SupportTicket(Base):
    """ISP Support Ticket model"""

    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
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
