"""
Session and User Management Service
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Tuple

from sqlalchemy.orm import Session as DBSession

from ..models import Conversation, ConversationStatus, User


class SessionService:
    """Unified session and user management"""

    def get_or_create_user(self, phone: str, db: DBSession) -> Tuple[User, bool]:
        """Get existing user or create new one"""
        user = db.query(User).filter(User.phone == phone).first()
        is_new = False

        if not user:
            user = User(
                phone=phone,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                total_conversations=0,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            is_new = True
        else:
            user.last_seen = datetime.utcnow()
            db.commit()

        return user, is_new

    def get_or_create_conversation(self, phone: str, db: DBSession) -> Conversation:
        """Get active conversation or create new one"""
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.phone == phone,
                Conversation.status.in_(
                    [ConversationStatus.active, ConversationStatus.idle]
                ),
            )
            .order_by(Conversation.last_activity.desc())
            .first()
        )

        # Check TTL expiration
        if conversation and datetime.utcnow() > conversation.ttl_expires_at:
            conversation.status = ConversationStatus.closed
            db.commit()
            conversation = None

        # Create new if needed
        if not conversation:
            user = db.query(User).filter(User.phone == phone).first()
            tid = f"{phone.replace('+', '')}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

            conversation = Conversation(
                id=tid,
                user_id=user.id if user else 0,
                phone=phone,
                status=ConversationStatus.active,
                state="idle",
                ttl_expires_at=datetime.utcnow() + timedelta(hours=24),
            )
            db.add(conversation)

            if user:
                user.total_conversations += 1

            db.commit()
            db.refresh(conversation)

        # Update activity
        conversation.last_activity = datetime.utcnow()
        if conversation.status == ConversationStatus.idle:
            conversation.status = ConversationStatus.active
        db.commit()

        return conversation

    def update_state(
        self,
        conversation: Conversation,
        state: str,
        db: DBSession,
        context: Dict | None = None,
    ) -> None:
        """Update conversation state and optional context"""
        conversation.state = state

        if context:
            ctx = conversation.context or {}
            ctx.update(context)
            conversation.context = ctx

        db.commit()


session_service = SessionService()
