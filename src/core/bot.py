"""
Core Bot Logic: NLP, WhatsApp Client, Sessions, and Message Processing
Consolidated from src/backend/
"""
import re
import uuid
import httpx
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from base64 import b64encode
from sqlalchemy.orm import Session as DBSession

from .config import settings, business_config, get_logger, is_business_open, get_business_hours_message, sanitize_input
from .database import Conversation, ConversationStatus, User, Message, get_db_context
from .knowledge import support_service

logger = get_logger(__name__)

# ============================================================================
# NLP SERVICE
# ============================================================================

class NLPService:
    """Intent classification and language utilities"""
    
    ALLOWED_INTENTS = {
        "greeting", "support", "hours", "payment", 
        "help", "thanks", "farewell", "complaint", 
        "affirmative", "negative", "plans", "billing"
    }
    
    def __init__(self):
        self.intent_patterns = {
            "greeting": [r"\b(hola|buenos días|buenas tardes|buenas noches|hey|hi|hello|saludos)\b"],
            "support": [
                r"\b(soporte|ayuda técnica|asistencia técnica|problema técnico|no funciona|no enciende|no prende|fallo|falla)\b",
                r"\b(internet|conexión|conexion|router|módem|modem|wifi|velocidad|luz roja|los roja)\b",
                r"\b(agua|mojó|mojo|caída|caida|lento|lentitud)\b"
            ],
            "plans": [r"\b(plan|planes|paquete|paquetes|fibra|megas|mb)\b"],
            "billing": [r"\b(factura|pago|recibo|cuenta|deuda|saldo)\b"],
            "hours": [r"\b(horario|hora|abierto|cerrado|atienden|atención)\b"],
            "payment": [r"\b(pago|pagar|efectivo|tarjeta|transferencia)\b"],
            "help": [r"\b(ayuda|help|asistencia|información|informacion)\b"],
            "thanks": [r"\b(gracias|thank|agradezco)\b"],
            "farewell": [r"\b(adiós|adios|chao|hasta luego|bye)\b"],
            "complaint": [r"\b(queja|reclamo|malo|terrible|pésimo|pesimo)\b"],
            "affirmative": [r"\b(sí|si|yes|ok|okay|vale|dale|perfecto|claro|correcto|confirmar)\b"],
            "negative": [
                r"^(no|nop|nope|nunca|jamás|jamas|negativo)$",
                r"\b(cancelar|detener|parar)\b"
            ]
        }
    
    def classify_intent(self, message: str) -> str:
        """Classify intent from message"""
        msg = message.lower().strip()
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, msg):
                    return intent
        return "unknown"

nlp_service = NLPService()

# ============================================================================
# WHATSAPP CLIENT (TWILIO)
# ============================================================================

class WhatsAppClient:
    """Twilio WhatsApp integration"""
    def __init__(self):
        if not settings.twilio_account_sid: return
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}"
        auth_string = f"{settings.twilio_account_sid}:{settings.twilio_auth_token}"
        self.auth_header = b64encode(auth_string.encode()).decode()
        self.headers = {"Authorization": f"Basic {self.auth_header}", "Content-Type": "application/x-www-form-urlencoded"}

    async def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send text message"""
        to_number = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        payload = {"From": settings.twilio_phone_number, "To": to_number, "Body": message}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/Messages.json", data=payload, headers=self.headers, timeout=30.0)
            return response.json()

    async def send_interactive_buttons(self, to: str, body: str, buttons: List[Dict[str, str]], header: str = None) -> Dict[str, Any]:
        """Fallback to numbered text for buttons"""
        msg = f"*{header}*\n\n" if header else ""
        msg += f"{body}\n\n"
        for idx, btn in enumerate(buttons[:10], 1):
            msg += f"{idx}. {btn.get('title')}\n"
        msg += "\nResponda con el número de su opción."
        return await self.send_text_message(to, msg)

whatsapp_client = WhatsAppClient()

# ============================================================================
# SESSION MANAGER
# ============================================================================

class SessionManager:
    """Lifecycle and state management"""
    def get_or_create_conversation(self, phone: str, db: DBSession) -> Conversation:
        conversation = db.query(Conversation).filter(
            Conversation.phone == phone,
            Conversation.status.in_([ConversationStatus.ACTIVE, ConversationStatus.IDLE])
        ).order_by(Conversation.last_activity.desc()).first()
        
        if conversation and datetime.utcnow() > conversation.ttl_expires_at:
            conversation.status = ConversationStatus.CLOSED
            db.commit()
            conversation = None
        
        if not conversation:
            user = db.query(User).filter(User.phone == phone).first()
            tid = f"{phone.replace('+','')}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
            conversation = Conversation(
                id=tid, user_id=user.id if user else 0, phone=phone,
                status=ConversationStatus.ACTIVE, state="idle",
                ttl_expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(conversation)
            if user: user.total_conversations += 1
            db.commit()
            db.refresh(conversation)
        
        conversation.last_activity = datetime.utcnow()
        if conversation.status == ConversationStatus.IDLE: conversation.status = ConversationStatus.ACTIVE
        db.commit()
        return conversation

    def update_state(self, conversation: Conversation, state: str, db: DBSession, context: Dict = None):
        conversation.state = state
        if context:
            ctx = conversation.context or {}
            ctx.update(context)
            conversation.context = ctx
        db.commit()

session_manager = SessionManager()

# ============================================================================
# USER SERVICE
# ============================================================================

class UserService:
    """User profile management"""
    def get_or_create_user(self, phone: str, db: DBSession) -> Tuple[User, bool]:
        user = db.query(User).filter(User.phone == phone).first()
        is_new = False
        if not user:
            user = User(phone=phone, first_seen=datetime.utcnow(), last_seen=datetime.utcnow(), total_conversations=0)
            db.add(user)
            db.commit()
            db.refresh(user)
            is_new = True
        else:
            user.last_seen = datetime.utcnow()
            db.commit()
        return user, is_new

user_service = UserService()

# ============================================================================
# MESSAGE PROCESSOR
# ============================================================================

class MessageProcessor:
    """Main Orchestrator"""
    async def process_message(self, phone: str, message: str, external_id: str = None):
        message = sanitize_input(message)
        with get_db_context() as db:
            user, _ = user_service.get_or_create_user(phone, db)
            conversation = session_manager.get_or_create_conversation(phone, db)
            
            # Idempotency check
            if external_id and db.query(Message).filter(Message.id == external_id).first():
                return

            self._log_message(conversation, "user", message, external_id, db)
            intent = nlp_service.classify_intent(message)
            
            if conversation.state == "idle":
                if intent == "support": await self.start_support(phone)
                elif intent == "plans": await self.show_plans(phone)
                elif intent == "billing": await self.show_billing_info(phone)
                elif intent == "greeting": await self.send_welcome_menu(phone)
                else: await self.handle_idle_state(phone, message)
            elif conversation.state == "technical_support":
                await self.handle_support_query_v2(phone, message, conversation, db)
            else:
                await self.handle_idle_state(phone, message)

    def _log_message(self, conversation: Conversation, sender: str, content: str, external_id: str, db: DBSession):
        msg_id = external_id or f"bot_{int(datetime.utcnow().timestamp())}_{conversation.id[:8]}"
        msg = Message(
            id=msg_id, conversation_id=conversation.id, sender=sender,
            direction="inbound" if sender == "user" else "outbound",
            message_type="text", content=content
        )
        db.add(msg)
        db.commit()

    async def send_welcome_menu(self, phone: str):
        business = business_config.get("business", {})
        welcome = f"Bienvenido al servicio de atención de *{business.get('name')}* 🌐\n\n¿En qué podemos ayudarle el día de hoy?"
        buttons = [{"id": "soporte", "title": "🔧 Soporte Técnico"}, {"id": "planes", "title": "📡 Ver Planes"}, {"id": "factura", "title": "💳 Facturación"}]
        await whatsapp_client.send_interactive_buttons(phone, welcome, buttons, "Menú de Inicio")

    async def start_support(self, phone: str):
        with get_db_context() as db:
            conversation = session_manager.get_or_create_conversation(phone, db)
            session_manager.update_state(conversation, "technical_support", db)
        msg = "🔧 *Centro de Soporte Técnico*\n\nPor favor, describa detalladamente el inconveniente que presenta (ej: 'No tengo servicio')."
        await whatsapp_client.send_text_message(phone, msg)

    async def handle_support_query_v2(self, phone: str, message: str, conversation: Conversation, db: DBSession):
        if message.lower() in ["salir", "cancelar", "menu"]:
            session_manager.update_state(conversation, "idle", db)
            await self.send_welcome_menu(phone)
            return

        ctx = conversation.context or {}
        history = ctx.get("chat_history", [])
        response = await support_service.get_ai_response(message, history)
        self._log_message(conversation, "bot", response, None, db)
        
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        session_manager.update_state(conversation, "technical_support", db, {"chat_history": history[-6:]})
        await whatsapp_client.send_text_message(phone, response)

    async def handle_idle_state(self, phone: str, message: str):
        business = business_config.get("business", {})
        welcome = f"Estimado cliente, bienvenido al soporte técnico de *{business.get('name')}* 🌐\n\nEscriba: *soporte*, *planes* o *factura*."
        await whatsapp_client.send_text_message(phone, welcome)

    async def show_plans(self, phone: str):
        await whatsapp_client.send_text_message(phone, "📡 *Planes de Fibra Óptica*\n\n1. *Básico (100MB)* - $20/mes\n2. *Pro (300MB)* - $35/mes\n3. *Gamer (600MB)* - $50/mes")

    async def show_billing_info(self, phone: str):
        await whatsapp_client.send_text_message(phone, "💳 *Pagos*\n\nPuedes pagar vía App, Transferencia o Puntos autorizados.")

message_processor = MessageProcessor()
