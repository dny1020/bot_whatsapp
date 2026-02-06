"""
Manejador de mensajes - Navegación dinámica de flujos
"""

from datetime import datetime

from .settings import business_config, flows_config, sanitize_input, get_logger
from .db import get_db_session
from .models import Message
from .services import whatsapp, session, llm

logger = get_logger(__name__)

# Comandos para volver al menú principal
EXIT_COMMANDS = ["salir", "cancelar", "menu", "inicio", "0"]


async def process_message(phone, message, external_id=None):
    """Procesar mensaje entrante de WhatsApp"""
    message = sanitize_input(message)
    db = get_db_session()

    try:
        user, _ = session.get_or_create_user(phone, db)
        conversation = session.get_or_create_conversation(phone, db)

        # Verificar duplicado
        if external_id:
            existing = db.query(Message).filter(Message.id == external_id).first()
            if existing:
                return

        _save_message(conversation, "user", message, external_id, db)

        # Obtener estado actual del flujo
        context = conversation.context or {}
        current_flow = context.get("current_flow", "welcome")
        
        # Verificar si quiere salir al menú
        if message.lower().strip() in EXIT_COMMANDS:
            await _go_to_flow(phone, "welcome", conversation, db)
            return

        # Obtener el flujo actual
        flow_data = flows_config.get("flows", {}).get(current_flow, {})
        buttons = flow_data.get("buttons", [])

        # Si el flujo actual tiene botones, intentar navegar
        if buttons:
            next_flow = _get_next_flow_from_input(message, buttons)
            
            if next_flow:
                await _go_to_flow(phone, next_flow, conversation, db)
                return

        # Si estamos en un flujo de soporte y no hay navegación, usar LLM
        if current_flow.startswith("support_"):
            await _handle_llm_support(phone, message, conversation, db)
            return

        # Si no hay match, mostrar el flujo actual de nuevo o el fallback
        if current_flow == "welcome":
            await _go_to_flow(phone, "welcome", conversation, db)
        else:
            # Mostrar mensaje de no entendido y el flujo actual
            fallback = flows_config.get("defaults", {}).get("fallback", "No entendí su respuesta.")
            await whatsapp.send_message(phone, fallback)
            await _show_flow(phone, current_flow)

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
    finally:
        db.close()


def _get_next_flow_from_input(message, buttons):
    """Determinar el siguiente flujo basado en el input del usuario"""
    message = message.strip()
    
    # Intentar por número (1, 2, 3...)
    if message.isdigit():
        index = int(message) - 1
        if 0 <= index < len(buttons):
            return buttons[index].get("id")
    
    # Intentar por título exacto o parcial
    message_lower = message.lower()
    for btn in buttons:
        title = btn.get("title", "").lower()
        # Quitar emojis para comparar
        title_clean = ''.join(c for c in title if ord(c) < 128).strip().lower()
        if message_lower == title_clean or message_lower in title_clean:
            return btn.get("id")
    
    return None


async def _go_to_flow(phone, flow_id, conversation, db):
    """Navegar a un flujo específico"""
    session.update_conversation_state(
        conversation, 
        conversation.state, 
        db, 
        {"current_flow": flow_id}
    )
    await _show_flow(phone, flow_id)


async def _show_flow(phone, flow_id):
    """Mostrar un flujo (con botones o solo texto)"""
    flow_data = flows_config.get("flows", {}).get(flow_id, {})
    
    if not flow_data:
        # Flujo no existe, mostrar welcome
        flow_data = flows_config.get("flows", {}).get("welcome", {})
        flow_id = "welcome"
    
    # Obtener texto y reemplazar variables
    business = business_config.get("business", {})
    text = flow_data.get("text", "")
    text = text.replace("{business_name}", business.get("name", "nuestra empresa"))
    
    buttons = flow_data.get("buttons", [])
    header = flow_data.get("header", "")
    
    if buttons:
        # Flujo con opciones
        await whatsapp.send_menu(phone, text, buttons, header)
    else:
        # Flujo terminal (solo texto)
        await whatsapp.send_message(phone, text)


async def _handle_llm_support(phone, message, conversation, db):
    """Manejar consulta de soporte con LLM"""
    context = conversation.context or {}
    history = context.get("chat_history", [])

    # Obtener respuesta de IA
    response = await llm.get_llm_response(message, history)
    _save_message(conversation, "bot", response, None, db)

    # Actualizar historial
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    
    session.update_conversation_state(
        conversation, 
        conversation.state, 
        db, 
        {
            "chat_history": history[-6:],
            "current_flow": context.get("current_flow", "support_lvl1")
        }
    )

    await whatsapp.send_message(phone, response)


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
