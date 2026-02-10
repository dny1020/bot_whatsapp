"""
Manejador de mensajes - Navegacion dinamica de flujos con inteligencia local
"""

from datetime import datetime

from .settings import business_config, flows_config, sanitize_input, get_logger
from .db import get_db_session
from .models import Message
from .services import whatsapp, session, llm
from .services.intelligence import (
    fuzzy_match_option,
    check_keyword_trigger,
    analyze_sentiment,
    get_empathetic_prefix,
    get_cached_response,
    cache_response,
    extract_entities,
    extract_nickname,
    get_progressive_response,
    detect_topic_for_progressive,
    adjust_response_length
)

logger = get_logger(__name__)

# Comandos para volver al menu (configurables desde settings.json)
EXIT_COMMANDS = business_config.get("bot", {}).get(
    "exit_commands", ["salir", "cancelar", "menu", "inicio", "0", "volver", "atras"]
)


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

        # Obtener contexto
        context = conversation.context or {}
        current_flow = context.get("current_flow", "welcome")
        nickname = context.get("nickname")
        
        # Extraer nickname si no lo tenemos
        if not nickname:
            nickname = extract_nickname(message)
            if nickname:
                logger.info(f"Nickname extraido: {nickname}")
                context["nickname"] = nickname
                session.update_conversation_state(conversation, conversation.state, db, context)
        
        # 1. Verificar si quiere salir al menu
        if message.lower().strip() in EXIT_COMMANDS:
            await _go_to_flow(phone, "welcome", conversation, db, nickname)
            return

        # 2. Verificar keyword triggers (respuestas automaticas)
        trigger_response = check_keyword_trigger(message)
        if trigger_response is not False:
            if trigger_response is None:
                await _go_to_flow(phone, "welcome", conversation, db, nickname)
            else:
                response = _personalize_response(trigger_response, nickname)
                _save_message(conversation, "bot", response, None, db)
                await whatsapp.send_message(phone, response)
            return

        # 3. Obtener el flujo actual
        flow_data = flows_config.get("flows", {}).get(current_flow, {})
        buttons = flow_data.get("buttons", [])

        # 4. Si el flujo actual tiene botones, intentar navegar
        if buttons:
            next_flow = _get_next_flow_from_input(message, buttons)
            
            if next_flow:
                await _go_to_flow(phone, next_flow, conversation, db, nickname)
                return

        # 5. Si estamos en un flujo de soporte y no hay navegacion, usar LLM
        if current_flow.startswith("support_"):
            await _handle_llm_support(phone, message, conversation, db, nickname)
            return

        # 6. Si no hay match, mostrar el flujo actual de nuevo o el fallback
        if current_flow == "welcome":
            await _go_to_flow(phone, "welcome", conversation, db, nickname)
        else:
            fallback = flows_config.get("defaults", {}).get("fallback", "No entendi su respuesta.")
            fallback = _personalize_response(fallback, nickname)
            await whatsapp.send_message(phone, fallback)
            await _show_flow(phone, current_flow, nickname)

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
    finally:
        db.close()


def _get_next_flow_from_input(message, buttons):
    """Determinar el siguiente flujo basado en el input del usuario"""
    message = message.strip().lower()
    
    # 1. Intentar por numero (1, 2, 3...)
    if message.isdigit():
        index = int(message) - 1
        if 0 <= index < len(buttons):
            return buttons[index].get("id")
    
    # 2. Intentar por texto exacto o parcial
    for btn in buttons:
        title = btn.get("title", "").lower()
        if message in title or title in message:
            return btn.get("id")
    
    # 3. Fuzzy matching para typos
    titles = [btn.get("title", "") for btn in buttons]
    match, score = fuzzy_match_option(message, titles, threshold=70)
    
    if match:
        logger.info(f"Fuzzy match: '{message}' -> '{match}' (score: {score})")
        for btn in buttons:
            if btn.get("title") == match:
                return btn.get("id")
    
    return None


def _personalize_response(text, nickname=None):
    """Personalizar respuesta con el nombre del usuario"""
    if not nickname:
        return text
    # Si el texto empieza con saludo, agregar nombre
    greetings = ["hola", "bienvenido", "gracias"]
    text_lower = text.lower()
    for greeting in greetings:
        if text_lower.startswith(greeting):
            return text.replace(greeting.capitalize(), f"{greeting.capitalize()} {nickname}", 1)
    return text


async def _go_to_flow(phone, flow_id, conversation, db, nickname=None):
    """Navegar a un flujo especifico"""
    session.update_conversation_state(
        conversation, 
        conversation.state, 
        db, 
        {"current_flow": flow_id}
    )
    await _show_flow(phone, flow_id, nickname)


async def _show_flow(phone, flow_id, nickname=None):
    """Mostrar un flujo (con botones o solo texto)"""
    flow_data = flows_config.get("flows", {}).get(flow_id, {})
    
    if not flow_data:
        flow_data = flows_config.get("flows", {}).get("welcome", {})
        flow_id = "welcome"
    
    # Obtener texto y reemplazar variables
    business = business_config.get("business", {})
    text = flow_data.get("text", "")
    text = text.replace("{business_name}", business.get("name", "nuestra empresa"))
    
    # Personalizar con nickname
    if nickname and flow_id == "welcome":
        text = text.replace("Bienvenido", f"Hola {nickname}! Bienvenido")
    
    buttons = flow_data.get("buttons", [])
    header = flow_data.get("header", "")
    
    if buttons:
        await whatsapp.send_menu(phone, text, buttons, header)
    else:
        await whatsapp.send_message(phone, text)


async def _handle_llm_support(phone, message, conversation, db, nickname=None):
    """Manejar consulta de soporte con LLM + inteligencia local"""
    context = conversation.context or {}
    history = context.get("chat_history", [])
    
    # Detectar tema para respuestas progresivas
    topic = detect_topic_for_progressive(message)
    
    # Verificar si hay respuesta progresiva para este tema
    if topic:
        topic_counts = context.get("topic_counts", {})
        interaction_count = topic_counts.get(topic, 0) + 1
        topic_counts[topic] = interaction_count
        
        # Guardar conteo
        context["topic_counts"] = topic_counts
        session.update_conversation_state(conversation, conversation.state, db, context)
        
        # Obtener respuesta progresiva
        progressive_response = get_progressive_response(topic, interaction_count)
        if progressive_response:
            response = _personalize_response(progressive_response, nickname)
            _save_message(conversation, "bot", response, None, db)
            await whatsapp.send_message(phone, response)
            return

    # Analizar sentimiento
    sentiment = analyze_sentiment(message)
    empathetic_prefix = get_empathetic_prefix(sentiment)
    
    # Extraer entidades (telefono, email, etc)
    entities = extract_entities(message)
    if entities:
        logger.info(f"Entidades extraidas: {entities}")
        context["entities"] = {**context.get("entities", {}), **entities}

    # Verificar cache primero
    cached = get_cached_response(message)
    if cached:
        response = empathetic_prefix + cached if empathetic_prefix else cached
    else:
        # Obtener respuesta de LLM
        response = await llm.get_llm_response(message, history)
        
        # Guardar en cache si no es muy especifica
        if len(message.split()) <= 10:
            cache_response(message, response)
        
        # Agregar prefijo empatico si es necesario
        if empathetic_prefix:
            response = empathetic_prefix + response

    # 4. Language Mirroring: Ajustar longitud según input del usuario
    response = adjust_response_length(response, len(message))

    _save_message(conversation, "bot", response, None, db)

    # Actualizar historial y contexto
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    
    new_context = {
        "chat_history": history[-6:],
        "current_flow": context.get("current_flow", "support_lvl1"),
        "sentiment_history": context.get("sentiment_history", []) + [sentiment["polarity"]],
        "nickname": context.get("nickname"),
        "topic_counts": context.get("topic_counts", {})
    }
    
    if entities:
        new_context["entities"] = {**context.get("entities", {}), **entities}
    
    session.update_conversation_state(conversation, conversation.state, db, new_context)

    await whatsapp.send_message(phone, response)
    
    # Si necesita humano, notificar
    if sentiment.get("needs_human"):
        logger.warning(f"Usuario frustrado detectado: {phone}")
        # Aqui se podria escalar a un agente humano


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
