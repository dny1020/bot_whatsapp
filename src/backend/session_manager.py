"""
Session state management with Redis
"""
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis
from ..utils.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manage user sessions in Redis"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.session_ttl = 3600  # 1 hour
    
    def _get_key(self, phone: str) -> str:
        """Get Redis key for phone number"""
        return f"session:{phone}"
    
    def get_session(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get session data for phone number"""
        try:
            key = self._get_key(phone)
            data = self.redis_client.get(key)
            
            if data:
                session = json.loads(data)
                logger.info("session_retrieved", phone=phone, state=session.get("state"))
                return session
            
            return None
        except Exception as e:
            logger.error("session_get_error", phone=phone, error=str(e))
            return None
    
    def create_session(self, phone: str, initial_state: str = "idle") -> Dict[str, Any]:
        """Create new session"""
        session = {
            "phone": phone,
            "state": initial_state,
            "context": {},
            "created_at": datetime.utcnow().isoformat(),
            "last_message_at": datetime.utcnow().isoformat()
        }
        
        self.save_session(phone, session)
        logger.info("session_created", phone=phone, state=initial_state)
        return session
    
    def save_session(self, phone: str, session: Dict[str, Any]):
        """Save session data"""
        try:
            key = self._get_key(phone)
            session["last_message_at"] = datetime.utcnow().isoformat()
            
            self.redis_client.setex(
                key,
                self.session_ttl,
                json.dumps(session)
            )
            
            logger.debug("session_saved", phone=phone)
        except Exception as e:
            logger.error("session_save_error", phone=phone, error=str(e))
    
    def update_state(self, phone: str, new_state: str, context: Optional[Dict[str, Any]] = None):
        """Update session state"""
        session = self.get_session(phone)
        
        if not session:
            session = self.create_session(phone, new_state)
        else:
            session["state"] = new_state
        
        if context:
            session["context"].update(context)
        
        self.save_session(phone, session)
        logger.info("session_state_updated", phone=phone, new_state=new_state)
    
    def get_context(self, phone: str, key: str = None) -> Any:
        """Get session context data"""
        session = self.get_session(phone)
        
        if not session:
            return None
        
        context = session.get("context", {})
        
        if key:
            return context.get(key)
        
        return context
    
    def set_context(self, phone: str, key: str, value: Any):
        """Set session context data"""
        session = self.get_session(phone) or self.create_session(phone)
        
        if "context" not in session:
            session["context"] = {}
        
        session["context"][key] = value
        self.save_session(phone, session)
        logger.debug("session_context_updated", phone=phone, key=key)
    
    def clear_context(self, phone: str, key: Optional[str] = None):
        """Clear session context"""
        session = self.get_session(phone)
        
        if not session:
            return
        
        if key:
            session["context"].pop(key, None)
        else:
            session["context"] = {}
        
        self.save_session(phone, session)
        logger.debug("session_context_cleared", phone=phone, key=key)
    
    def delete_session(self, phone: str):
        """Delete session"""
        try:
            key = self._get_key(phone)
            self.redis_client.delete(key)
            logger.info("session_deleted", phone=phone)
        except Exception as e:
            logger.error("session_delete_error", phone=phone, error=str(e))
    
    def extend_session(self, phone: str):
        """Extend session TTL"""
        try:
            key = self._get_key(phone)
            self.redis_client.expire(key, self.session_ttl)
        except Exception as e:
            logger.error("session_extend_error", phone=phone, error=str(e))


# Global session manager instance
session_manager = SessionManager()
