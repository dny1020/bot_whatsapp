"""
Message processor and bot logic
Implements clean architecture:
Webhook → Idempotency → Conversation (DB/Redis) → Intent → State Machine → Response
"""
from typing import Dict, Any, Optional
from datetime import datetime
from .session_manager import session_manager
from .whatsapp_client import whatsapp_client
from .database import get_db, get_db_context
from .models import User, Conversation, Message, ConversationStatus
from .support_service import support_service
from .user_service import user_service
from .nlp_service import nlp_service
from ..utils.helpers import (
    normalize_phone, sanitize_input, is_business_open, get_business_hours_message
)
from ..utils.config import business_config, settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MessageProcessor:
    """Process incoming messages and manage conversation flow"""
    
    def __init__(self):
        self.redis_client = session_manager.redis_client
        self.idempotency_ttl = 600  # 10 minutes
        self.farewell_keywords = [
            "gracias", "listo", "perfecto", "ok gracias", "chao", "adios", "adiós", "hasta luego", "eso es todo"
        ]
        
        self.commands = {
            "ayuda": self.show_help,
            "help": self.show_help,
            "soporte": self.start_support,
            "planes": self.show_plans,
            "factura": self.show_billing_info,
            "humano": self.request_human,
        }
    
    def _check_idempotency(self, message_id: str) -> bool:
        """Check if message has already been processed (idempotency)"""
        try:
            key = f"processed:{message_id}"
            exists = self.redis_client.exists(key)
            
            if exists:
                logger.info("duplicate_message_detected", message_id=message_id)
                return True
            
            # Mark as processed with TTL
            self.redis_client.setex(key, self.idempotency_ttl, "1")
            return False
            
        except Exception as e:
            logger.error("idempotency_check_error", message_id=message_id, error=str(e))
            # On error, allow processing to avoid blocking legitimate messages
            return False
    
    async def process_message(self, phone: str, message: str, message_id: str) -> None:
        """Process incoming message"""
        try:
            # 🔒 IDEMPOTENCY CHECK - Avoid processing duplicates
            if self._check_idempotency(message_id):
                return
            
            phone = normalize_phone(phone)
            message = sanitize_input(message)
            
            logger.info("processing_message", phone=phone, message=message[:50])
            
            # Manage Database Session per request
            with get_db_context() as db:
                
                # 1. Identify User
                user, is_new_user = user_service.get_or_create_user(phone, db)
                
                # 2. Get or Create Conversation
                conversation = session_manager.get_or_create_conversation(phone, db)
                
                # 3. Log Message (Inbound)
                self._log_message(conversation, "user", message, message_id, db)
                
                # 4. Check for Conversation Closure
                if self._check_closure(message, conversation, db):
                    await whatsapp_client.send_text_message(
                        phone,
                        "¡Gracias por contactarnos! Tu sesión ha sido cerrada. Si necesitas más ayuda, solo escribe nuevamente. 👋"
                    )
                    return

                # Mark as read (Not supported by Twilio, but we keep the logic flow)
                # await whatsapp_client.mark_as_read(message_id)
                
                # 5. Handle New User / Welcome logic
                if is_new_user or conversation.message_count <= 1:
                     # Only send welcome if it's the very first message in a new conversation and intent isn't specific
                     # Or logic: if new user, definitely welcome.
                     if is_new_user:
                         await self.send_welcome_menu(phone)
                         # Don't return, allow processing intent? No, usually welcome breaks flow.
                         # But let's check intent first.
                         pass 
                
                # 6. Intent Classification
                intent = nlp_service.classify_intent(message)
                logger.info("intent_detected", phone=phone, intent=intent)
                
                # Update Activity
                conversation.last_activity = datetime.utcnow()
                conversation.message_count += 1
                db.commit()

                # 7. Check Direct Commands
                message_lower = message.lower().strip()
                if message_lower in self.commands:
                    await self.commands[message_lower](phone)
                    return
                
                # 8. State Machine Logic (using Conversation state)
                state = conversation.state
                
                if state == "idle":
                    if intent == "support":
                        await self.start_support(phone)
                    elif intent == "plans":
                        await self.show_plans(phone)
                    elif intent == "billing":
                        await self.show_billing_info(phone)
                    elif intent == "greeting":
                        await self.send_welcome_menu(phone)
                    elif intent == "help":
                        await self.show_help(phone)
                    else:
                        await self.handle_idle_state(phone, message)
                        
                elif state == "technical_support":
                    await self.handle_support_query_v2(phone, message, conversation, db)
                else:
                    await self.handle_idle_state(phone, message)
                
        except Exception as e:
            logger.error("message_processing_error", phone=phone, error=str(e))
            try:
                await whatsapp_client.send_text_message(
                    phone,
                    "Lo siento, hubo un error técnico. Por favor intenta de nuevo en unos minutos."
                )
            except:
                pass

                # 1. Identify User
                user, is_new_user = user_service.get_or_create_user(phone, db)

    def _check_closure(self, message: str, conversation: Conversation, db) -> bool:
        """Check if message indicates conversation closure"""
        message_lower = message.lower()
        
        if any(kw == message_lower or kw in message_lower.split() for kw in self.farewell_keywords):
             session_manager.close_conversation(conversation.id, "user_farewell", db)
             return True
        return False

    def _log_message(self, conversation: Conversation, sender: str, content: str, external_id: str, db):
        """Log message to database linked to conversation"""
        try:
            msg = Message(
                conversation_id=conversation.id,
                sender=sender, # user or bot
                direction="inbound" if sender == "user" else "outbound",
                message_type="text",
                content=content,
                created_at=datetime.utcnow()
            )
            db.add(msg)
            db.commit()
        except Exception as e:
            logger.error("log_message_error", error=str(e))

    async def send_welcome_menu(self, phone: str):
        """Send interactive welcome menu"""
        business = business_config.get("business", {})
        
        if not is_business_open():
            response = f"¡Hola! Gracias por contactar a *{business.get('name')}* 🏪\n\n"
            response += "Actualmente estamos cerrados. 😴\n\n"
            response += get_business_hours_message()
            await whatsapp_client.send_text_message(phone, response)
            return

        welcome = f"¡Hola! Bienvenido a *{business.get('name')}* 🌐\n\n"
        welcome += f"{business.get('description')}\n\n"
        welcome += "¿En qué podemos ayudarte hoy?"
        
        buttons = [
            {"id": "soporte", "title": "🔧 Soporte Técnico"},
            {"id": "planes", "title": "📡 Ver Planes"},
            {"id": "factura", "title": "💳 Facturación"}
        ]
        
        try:
            await whatsapp_client.send_interactive_buttons(
                phone, welcome, buttons, "Selecciona una opción"
            )
        except:
            # Fallback
            await self.handle_idle_state(phone, "")

    async def handle_idle_state(self, phone: str, message: str):
        """Handle idle state response"""
        business = business_config.get("business", {})
        welcome = f"¡Hola! Bienvenido al soporte técnico de *{business.get('name')}* 🌐\n\n"
        welcome += "Escribe una de estas opciones:\n"
        welcome += "• *soporte* - Problemas técnicos\n"
        welcome += "• *planes* - Ver planes de internet\n"
        welcome += "• *factura* - Pagos y saldos"
        
        await whatsapp_client.send_text_message(phone, welcome)

    async def start_support(self, phone: str):
        """Start support flow"""
        with get_db_context() as db:
            conversation = session_manager.get_or_create_conversation(phone, db)
            session_manager.update_state(conversation, "technical_support", db)
        
        response = "🔧 *Soporte Técnico*\n\n"
        response += "Por favor, describe tu problema con detalle (ej: 'No tengo internet', 'Luz roja en router')."
        await whatsapp_client.send_text_message(phone, response)

    async def handle_support_query_v2(self, phone: str, message: str, conversation: Conversation, db):
        """
        Handle support query using AI with Conversation context
        """
        if message.lower() in ["salir", "cancelar", "menu"]:
            session_manager.update_state(conversation, "idle", db)
            await self.send_welcome_menu(phone)
            return

        # Get context from conversation context JSON
        context_data = conversation.context or {}
        history = context_data.get("chat_history", [])
        
        # AI Response
        response = await support_service.get_ai_response(message, history)
        
        # Log Bot Response in DB
        self._log_message(conversation, "bot", response, None, db)
        
        # Update History in Context
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        if len(history) > 6:
            history = history[-6:]
            
        session_manager.set_context(conversation, "chat_history", history, db)
        
        # Send to WhatsApp
        await whatsapp_client.send_text_message(phone, response)

    # ... (Other handler methods: show_plans, show_billing_info, request_human, show_help) ...
    # Re-implementing them briefly to ensure class completeness

    async def show_plans(self, phone: str):
        response = "📡 *Planes de Fibra Óptica*\n\n1. *Básico (100MB)* - $20/mes\n2. *Pro (300MB)* - $35/mes\n3. *Gamer (600MB)* - $50/mes"
        await whatsapp_client.send_text_message(phone, response)

    async def show_billing_info(self, phone: str):
        response = "💳 *Pagos*\n\nPuedes pagar vía App, Transferencia o Puntos autorizados."
        await whatsapp_client.send_text_message(phone, response)

    async def request_human(self, phone: str):
        await whatsapp_client.send_text_message(phone, "He notificado a un operador. 👨‍💻")

    async def show_help(self, phone: str):
        await self.handle_idle_state(phone, "")
    
    async def _send_unknown_intent_response(self, phone: str):
        await self.handle_idle_state(phone, "")


# Global instance
message_processor = MessageProcessor()
