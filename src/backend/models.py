"""
Database models for ISP Support Chatbot
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    IDLE = "idle"
    CLOSED = "closed"
    ARCHIVED = "archived"


class User(Base):
    """User/Customer model - ISP Support"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100))
    nickname = Column(String(100)) # New
    email = Column(String(100))
    
    # Activity Stats
    first_seen = Column(DateTime, default=datetime.utcnow) # New
    last_seen = Column(DateTime, default=datetime.utcnow) # New
    total_conversations = Column(Integer, default=0) # New
    is_active = Column(Boolean, default=True) # New
    language = Column(String(10), default="es") # New
    preferences = Column(JSON, default={}) # New

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    support_tickets = relationship("SupportTicket", back_populates="user")


class Conversation(Base):
    """Chat conversation model (Enhanced Session)"""
    __tablename__ = "conversations"
    
    id = Column(String(100), primary_key=True, index=True) # Changed from auto-increment Int to String UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone = Column(String(20), index=True, nullable=False)
    
    # State tracking
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE, index=True) # New
    state = Column(String(50), default="idle")  # internal FSM state (e.g. browsing_menu)
    context = Column(JSON, default={})  # Session context data
    
    # Usage metrics
    message_count = Column(Integer, default=0) # New
    topic = Column(String(200)) # New
    
    # Timestamps
    last_activity = Column(DateTime, default=datetime.utcnow) # New (Renamed from last_message_at?) No, explicit last activity
    ttl_expires_at = Column(DateTime) # New
    closed_at = Column(DateTime) # New
    close_reason = Column(String(50)) # New
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Message log"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), ForeignKey("conversations.id"), nullable=False) # Changed from session_id
    
    sender = Column(String(20))  # 'user' or 'bot' # New
    direction = Column(String(10))  # inbound, outbound (Keep for compatibility or migrate to sender?) user=inbound, bot=outbound. Keeping for now.
    message_type = Column(String(20))  # text, image, interactive, etc.
    content = Column(Text)
    
    # Metrics
    tokens_used = Column(Integer, default=0) # New
    latency_ms = Column(Integer, default=0) # New
    
    meta_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class SupportTicket(Base):
    """ISP Support Ticket model"""
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Ticket details
    issue_type = Column(String(50))  # connectivity, billing, technical, general
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    subject = Column(String(200))
    description = Column(Text)
    
    # Status tracking
    status = Column(String(20), default="open")  # open, in_progress, resolved, closed
    
    # Resolution
    resolution = Column(Text)
    resolved_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="support_tickets")
