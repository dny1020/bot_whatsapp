"""
Manejador de mensajes
"""

from datetime import datetime

from .settings import business_config, flows_config, sanitize_input, get_logger
from .db import get_db_session
from .models import Message
from .services import whatsapp, session, llm

logger = get_logger(__name__)


async def process_message(phone, message, external_id=None):
    """Procesar mensaje entrante de WhatsApp"""
    message = sanitize_input(message)
    db = get_db_session()

    try:
        # Obtener o crear usuario y conversación
        user, _ = session.get_or_create_user(phone, db)
        conversation = session.get_or_create_conversation(phone, db)

        # Verificar que no sea duplicado
        if external_id:
            existing = db.query(Message).filter(Message.id == external_id).first()
            if existing:
                return

        # Guardar mensaje del usuario
        _save_message(conversation, "user", message, external_id, db)
        
        # Clasificar intención
        intent = llm.classify_intent(message)

        # Procesar según estado de la conversación
        if conversation.state == "idle":
            await _handle_idle(phone, intent, db)
        elif conversation.state == "technical_support":
            await _handle_support(phone, message, conversation, db)
        else:
            await _send_welcome_menu(phone)

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
    finally:
        db.close()


async def _handle_idle(phone, intent, db):
    """Manejar mensaje cuando la conversación está idle"""
    if intent == "support":
        await _start_support(phone, db)
    elif intent == "plans":
        await _show_plans(phone)
    elif intent == "billing":
        await _show_billing(phone)
    else:
        await _send_welcome_menu(phone)


async def _handle_support(phone, message, conversation, db):
    """Manejar mensaje en flujo de soporte técnico"""
    flow = flows_config.get("flows", {}).get("technical_support", {})
    exit_commands = flow.get("exit_commands", ["salir", "cancelar", "menu"])

    # Verificar si quiere salir
    if message.lower() in exit_commands:
        session.update_conversation_state(conversation, "idle", db)
        await _send_welcome_menu(phone)
        return

    # Obtener historial de chat
    context = conversation.context or {}
    history = context.get("chat_history", [])

    # Obtener respuesta de IA
    response = await llm.get_llm_response(message, history)
    _save_message(conversation, "bot", response, None, db)

    # Actualizar historial
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    session.update_conversation_state(
        conversation, "technical_support", db, {"chat_history": history[-6:]}
    )

    await whatsapp.send_message(phone, response)


async def _send_welcome_menu(phone):
    """Enviar menú de bienvenida"""
    business = business_config.get("business", {})
    flow = flows_config.get("flows", {}).get("welcome", {})

    text = flow.get("text", "Bienvenido").replace(
        "{business_name}", business.get("name", "nuestra empresa")
    )
    buttons = flow.get("buttons", [])
    header = flow.get("header", "Menú")

    await whatsapp.send_menu(phone, text, buttons, header)


async def _start_support(phone, db):
    """Iniciar flujo de soporte técnico"""
    conversation = session.get_or_create_conversation(phone, db)
    session.update_conversation_state(conversation, "technical_support", db)

    flow = flows_config.get("flows", {}).get("technical_support", {})
    msg = flow.get("start_message", "🔧 *Soporte Técnico*\n\nPor favor, describa su problema.")

    await whatsapp.send_message(phone, msg)


async def _show_plans(phone):
    """Mostrar planes disponibles"""
    flow = flows_config.get("flows", {}).get("plans", {})
    msg = flow.get("text", "Consulte nuestros planes disponibles.")
    await whatsapp.send_message(phone, msg)


async def _show_billing(phone):
    """Mostrar información de facturación"""
    flow = flows_config.get("flows", {}).get("billing", {})
    msg = flow.get("text", "Información de facturación.")
    await whatsapp.send_message(phone, msg)


def _save_message(conversation, sender, content, external_id, db):
    """Guardar mensaje en la base de datos"""
    msg_id = external_id or f"bot_{int(datetime.utcnow().timestamp())}_{conversation.id[:8]}"
    
    msg = Message(
        id=msg_id,
        conversation_id=conversation.id,
        sender=sender,
        direction="inbound" if sender == "user" else "outbound",
        message_type="text",
        content=content,
    )
    db.add(msg)
    db.commit()
