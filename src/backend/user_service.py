"""
User Service
Handles user creation, identification, and profile management.
"""
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session as DBSession

from .models import User
from ..utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """Service to handle user operations"""
    
    def get_or_create_user(self, phone: str, db: DBSession) -> Tuple[User, bool]:
        """
        Get user by phone or create if not exists.
        Returns: (user, is_new)
        """
        user = db.query(User).filter(User.phone == phone).first()
        is_new = False
        
        if not user:
            user = User(
                phone=phone,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                total_conversations=0,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("user_created", phone=phone, id=user.id)
            is_new = True
        else:
            # Update last activity
            user.last_seen = datetime.utcnow()
            db.commit()
        
        return user, is_new

    def update_nickname(self, phone: str, nickname: str, db: DBSession) -> Optional[User]:
        """Update user alias/nickname"""
        user = db.query(User).filter(User.phone == phone).first()
        if user:
            user.nickname = nickname
            db.commit()
            db.refresh(user)
            logger.info("user_nickname_updated", phone=phone, nickname=nickname)
        return user

    def get_user_profile(self, phone: str, db: DBSession) -> Optional[dict]:
        """Get user profile data"""
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            return None
            
        return {
            "name": user.name or user.nickname,
            "phone": user.phone,
            "conversations": user.total_conversations,
            "first_seen": user.first_seen.isoformat() if user.first_seen else None
        }


# Global user service instance
user_service = UserService()
