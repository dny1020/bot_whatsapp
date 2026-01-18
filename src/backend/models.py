"""
Database models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User/Customer model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="user")
    orders = relationship("Order", back_populates="user")


class Session(Base):
    """Chat session model"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone = Column(String(20), index=True, nullable=False)
    state = Column(String(50), default="idle")  # idle, browsing_menu, ordering, confirming, etc.
    context = Column(JSON, default={})  # Session context data
    last_message_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")


class Message(Base):
    """Message log"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    direction = Column(String(10))  # inbound, outbound
    message_type = Column(String(20))  # text, image, interactive, etc.
    content = Column(Text)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="messages")


class Order(Base):
    """Order model"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Order details
    items = Column(JSON, nullable=False)  # List of ordered items
    subtotal = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    
    # Delivery information
    delivery_address = Column(Text)
    delivery_zone = Column(String(50))
    delivery_instructions = Column(Text)
    
    # Payment
    payment_method = Column(String(20))
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, confirmed, preparing, delivering, delivered, cancelled
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="orders")


class Product(Base):
    """Product/Menu item model"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(50), unique=True, index=True)
    category = Column(String(50))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    available = Column(Boolean, default=True)
    image_url = Column(String(500))
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
