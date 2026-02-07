"""
Servicio de sesiones y usuarios
"""

import uuid
from datetime import datetime, timedelta

from ..models import Conversation, User

def get_or_create_user(phone, db):
    """Obtener usuario existente o crear uno nuevo"""
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


def get_or_create_conversation(phone, db):
    """Obtener conversación activa o crear una nueva"""
    # Buscar conversación activa
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.phone == phone,
            Conversation.status.in_(["active", "idle"]),
        )
        .order_by(Conversation.last_activity.desc())
        .first()
    )

    # Verificar si expiró
    if conversation and conversation.ttl_expires_at:
        if datetime.utcnow() > conversation.ttl_expires_at:
            conversation.status = "closed"
            db.commit()
            conversation = None

    # Crear nueva si no existe
    if not conversation:
        user = db.query(User).filter(User.phone == phone).first()
        
        conv_id = f"{phone.replace('+', '')}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        conversation = Conversation(
            id=conv_id,
            user_id=user.id if user else 0,
            phone=phone,
            status="active",
            state="idle",
            ttl_expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(conversation)

        if user:
            user.total_conversations += 1

        db.commit()
        db.refresh(conversation)

    # Actualizar actividad
    conversation.last_activity = datetime.utcnow()
    if conversation.status == "idle":
        conversation.status = "active"
    db.commit()

    return conversation


def update_conversation_state(conversation, state, db, context=None):
    """Actualizar estado de la conversacion"""
    conversation.state = state

    if context:
        current_context = dict(conversation.context or {})
        current_context.update(context)
        conversation.context = current_context

    db.commit()
    db.refresh(conversation)
