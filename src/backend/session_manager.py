"""
Session state management with Redis and Database
"""
import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis
from sqlalchemy.orm import Session as DBSession

from ..utils.config import settings
from ..utils.logger import get_logger
from .models import Conversation, ConversationStatus, User
from .database import get_db

logger = get_logger(__name__)


class SessionManager:
    """Manage user conversations (lifecycle & state)"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        # Redis caching config
        self.active_conv_ttl = 86400  # 24 hours
        self.idle_timeout_seconds = 1800 # 30 mins
    
    def _get_redis_key(self, phone: str) -> str:
        """Get Redis key for active conversation ID"""
        return f"active_conversation:{phone}"

    def get_or_create_conversation(self, phone: str, db: DBSession) -> Conversation:
        """
        Get active conversation or create new one.
        Checks Redis cache first, then DB.
        """
        redis_key = self._get_redis_key(phone)
        conversation_id = self.redis_client.get(redis_key)
        
        conversation = None
        
        if conversation_id:
            # Check if exists in DB and is active
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.status != ConversationStatus.CLOSED,
                Conversation.status != ConversationStatus.ARCHIVED
            ).first()
            
            if not conversation:
                # Cache invalid
                self.redis_client.delete(redis_key)
        
        if not conversation:
            # Try to find active conversation in DB (fallback)
            conversation = db.query(Conversation).filter(
                Conversation.phone == phone,
                Conversation.status.in_([ConversationStatus.ACTIVE, ConversationStatus.IDLE])
            ).order_by(Conversation.last_activity.desc()).first()
            
            # Check if expired by TTL (24h)
            if conversation:
                if datetime.utcnow() > conversation.ttl_expires_at:
                    self.close_conversation(conversation.id, "ttl_expired", db)
                    conversation = None
        
        if not conversation:
            # Create NEW conversation
            conversation = self._create_new_conversation(phone, db)
        
        # Update Redis cache
        self.redis_client.setex(redis_key, self.active_conv_ttl, conversation.id)
        
        # Update last activity
        conversation.last_activity = datetime.utcnow()
        if conversation.status == ConversationStatus.IDLE:
             conversation.status = ConversationStatus.ACTIVE
        
        db.commit()
        db.refresh(conversation)
        
        return conversation

    def _create_new_conversation(self, phone: str, db: DBSession) -> Conversation:
        """Create a new conversation record"""
        # Ensure user exists (should be handled by caller, but safety check)
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
             # Just in case, though message_processor should handle user creation
             logger.warning("creating_conversation_for_unknown_user", phone=phone)
             # user creation should ideally be in user_service or similar
        
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_suffix = uuid.uuid4().hex[:6]
        conversation_id = f"{phone.replace('+','')}_{timestamp}_{unique_suffix}"
        
        new_conv = Conversation(
            id=conversation_id,
            user_id=user.id if user else 0, # Fallback if user logic separates
            phone=phone,
            status=ConversationStatus.ACTIVE,
            state="idle", # FSM state
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            ttl_expires_at=datetime.utcnow() + timedelta(hours=24),
            message_count=0
        )
        
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        
        logger.info("conversation_created", id=conversation_id, phone=phone)
        
        # Update User stats
        if user:
            user.total_conversations += 1
            user.last_seen = datetime.utcnow()
            db.commit()

        return new_conv

    def close_conversation(self, conversation_id: str, reason: str, db: DBSession):
        """Close a conversation explicitly"""
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation and conversation.status != ConversationStatus.CLOSED:
            conversation.status = ConversationStatus.CLOSED
            conversation.closed_at = datetime.utcnow()
            conversation.close_reason = reason
            db.commit()
            
            # Clear Redis cache
            self.redis_client.delete(self._get_redis_key(conversation.phone))
            logger.info("conversation_closed", id=conversation_id, reason=reason)

    def mark_idle(self, conversation_id: str, db: DBSession):
        """Mark conversation as idle"""
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation and conversation.status == ConversationStatus.ACTIVE:
            conversation.status = ConversationStatus.IDLE
            db.commit()
            logger.info("conversation_idle", id=conversation_id)

    # --- Methods for FSM State (Backward Compatibility / Usage) ---
    
    def get_state(self, conversation: Conversation) -> str:
        return conversation.state

    def update_state(self, conversation: Conversation, new_state: str, db: DBSession, context_update: Dict = None):
        conversation.state = new_state
        if context_update:
            current_context = conversation.context or {}
            current_context.update(context_update)
            conversation.context = current_context
        
        conversation.last_activity = datetime.utcnow()
        db.commit()

    def get_context(self, conversation: Conversation) -> Dict:
        return conversation.context or {}
        
    def set_context(self, conversation: Conversation, key: str, value: Any, db: DBSession):
        current_context = conversation.context or {}
        current_context[key] = value
        conversation.context = current_context
        db.commit()


# Global session manager instance
session_manager = SessionManager()
