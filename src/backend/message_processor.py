"""
Message processor and bot logic
"""
from typing import Dict, Any, Optional
from datetime import datetime
from .session_manager import session_manager
from .whatsapp_client import whatsapp_client
from .database import get_db_context
from .support_service import support_service
from ..utils.helpers import (
    normalize_phone, sanitize_input
)
from ..utils.config import business_config, settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MessageProcessor:
    """Process incoming messages and manage conversation flow"""
    
    def __init__(self):
        self.commands = {
            "ayuda": self.show_help,
            "help": self.show_help,
            "soporte": self.start_support,
            "planes": self.show_plans,
            "factura": self.show_billing_info,
            "humano": self.request_human,
        }
    
    async def process_message(self, phone: str, message: str, message_id: str) -> None:
        """Process incoming message"""
        try:
            phone = normalize_phone(phone)
            message = sanitize_input(message)
            
            logger.info("processing_message", phone=phone, message=message[:50])
            
            # Get or create user
            user_created = await self._ensure_user_exists(phone)
            
            # Log message
            await self._log_message(phone, "inbound", "text", message, message_id)
            
            # Get session
            session = session_manager.get_session(phone)
            if not session:
                session = session_manager.create_session(phone)
                # If new user or first message, send welcome menu
                if user_created or not session.get("has_seen_welcome"):
                    await self.send_welcome_menu(phone)
                    session["has_seen_welcome"] = True
                    session_manager.save_session(phone, session)
                    return
            
            # Mark as read
            await whatsapp_client.mark_as_read(message_id)
            
            # Check for commands
            message_lower = message.lower().strip()
            
            if message_lower in self.commands:
                await self.commands[message_lower](phone)
                return
            
            # Process based on current state
            state = session.get("state", "idle")
            
            if state == "idle":
                await self.handle_idle_state(phone, message)
            elif state == "technical_support":
                await self.handle_support_query(phone, message)
            else:
                await self.handle_idle_state(phone, message)
                
        except Exception as e:
            logger.error("message_processing_error", phone=phone, error=str(e))
            await whatsapp_client.send_text_message(
                phone,
                "Lo siento, hubo un error procesando tu mensaje. Por favor intenta de nuevo."
            )
    
    async def send_welcome_menu(self, phone: str):
        """Send interactive welcome menu with buttons"""
        business = business_config.get("business", {})
        
        if not is_business_open():
            response = f"¡Hola! Gracias por contactar a *{business.get('name')}* 🏪\n\n"
            response += "Actualmente estamos cerrados. 😴\n\n"
            response += get_business_hours_message()
            response += "\n\n¡Te esperamos pronto!"
            await whatsapp_client.send_text_message(phone, response)
            return
        
        # Send welcome with interactive buttons
        welcome = f"¡Hola! Bienvenido a *{business.get('name')}* 🏪\n\n"
        welcome += f"{business.get('description')}\n\n"
        welcome += "¿Qué te gustaría hacer hoy?"
        
        buttons = [
            {"id": "soporte", "title": "🔧 Soporte Técnico"},
            {"id": "planes", "title": "📡 Ver Planes"},
            {"id": "factura", "title": "💳 Facturación"}
        ]
        
        try:
            await whatsapp_client.send_interactive_buttons(
                phone,
                body_text=welcome,
                buttons=buttons,
                footer_text="Escribe 'menu', 'pedido' o 'ayuda'"
            )
        except Exception as e:
            # Fallback to text if interactive fails
            logger.warning("interactive_menu_failed", error=str(e))
            await self.handle_idle_state(phone, "")
    
    async def handle_idle_state(self, phone: str, message: str):
        """Handle idle state - welcome message"""
        business = business_config.get("business", {})
        
        welcome = f"¡Hola! Bienvenido al soporte técnico de *{business.get('name')}* 🌐\n\n"
        welcome += "¿En qué puedo ayudarte hoy?\n\n"
        welcome += "Comandos disponibles:\n"
        welcome += "• *soporte* - Iniciar consulta técnica\n"
        welcome += "• *planes* - Ver planes de internet\n"
        welcome += "• *factura* - Información de pagos\n"
        welcome += "• *ayuda* - Más información"
        
        await whatsapp_client.send_text_message(phone, welcome)

    async def start_support(self, phone: str):
        """Start support conversation"""
        session_manager.update_state(phone, "technical_support")
        response = "🔧 *Soporte Técnico*\n\n"
        response += "Por favor, describe tu problema o consulta con el mayor detalle posible.\n"
        response += "Ejemplo: 'No tengo internet' o 'Mi conexión está lenta'."
        await whatsapp_client.send_text_message(phone, response)

    async def handle_support_query(self, phone: str, message: str):
        """Handle support query using Groq"""
        if message.lower() in ["salir", "cancelar", "terminar"]:
            session_manager.update_state(phone, "idle")
            await whatsapp_client.send_text_message(phone, "Has salido del soporte técnico. ¿En qué más puedo ayudarte?")
            return

        # Get chat history from session (if any)
        context = session_manager.get_context(phone)
        history = context.get("chat_history", [])
        
        # Get AI response
        response = await support_service.get_ai_response(message, history)
        
        # Update history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        
        # Keep history short (last 6 messages)
        if len(history) > 6:
            history = history[-6:]
            
        session_manager.set_context(phone, "chat_history", history)
        
        # Send response
        formatted_response = f"{response}\n\n"
        formatted_response += "_(Escribe 'salir' para terminar o sigue preguntando)_"
        await whatsapp_client.send_text_message(phone, formatted_response)

    async def show_plans(self, phone: str):
        """Show ISP plans"""
        response = "📡 *Nuestros Planes de Fibra Óptica*\n\n"
        response += "1. *Plan Básico*: 100MB Simétricos - $20/mes\n"
        response += "2. *Plan Pro*: 300MB Simétricos - $35/mes\n"
        response += "3. *Plan Gamer*: 600MB Simétricos - $50/mes\n\n"
        response += "Todos incluyen instalación gratuita y router Wi-Fi 6."
        await whatsapp_client.send_text_message(phone, response)

    async def show_billing_info(self, phone: str):
        """Show billing info"""
        response = "💳 *Información de Facturación*\n\n"
        response += "Puedes pagar tu recibo mediante:\n"
        response += "• App Mi Clientes (pago con tarjeta)\n"
        response += "• Transferencia Bancaria\n"
        response += "• Puntos de recaudación externos.\n\n"
        response += "Escribe tu número de cliente para consultar tu saldo (Próximamente)."
        await whatsapp_client.send_text_message(phone, response)

    async def request_human(self, phone: str):
        """Request human assistance"""
        await whatsapp_client.send_text_message(
            phone, 
            "He notificado a un operador técnico. En breve se pondrán en contacto contigo. 👨‍💻"
        )

    async def show_help(self, phone: str):
        """Show help message"""
        business = business_config.get("business", {})
        
        help_text = f"ℹ️ *Ayuda - {business.get('name')}*\n\n"
        help_text += "*Comandos disponibles:*\n\n"
        help_text += "• *soporte* - Iniciar consulta de soporte técnico\n"
        help_text += "• *planes* - Ver planes disponibles\n"
        help_text += "• *factura* - Métodos de pago\n"
        help_text += "• *humano* - Hablar con una persona\n"
        help_text += "• *ayuda* - Mostrar esta ayuda\n"
        
        await whatsapp_client.send_text_message(phone, help_text)
    
    async def _ensure_user_exists(self, phone: str) -> bool:
        """Ensure user exists in database. Returns True if user was created."""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.phone == phone).first()
                
                if not user:
                    user = User(phone=phone)
                    db.add(user)
                    db.commit()
                    logger.info("user_created", phone=phone)
                    return True
                
                return False
        except Exception as e:
            logger.error("user_creation_error", phone=phone, error=str(e))
            return False
    
    async def _log_message(
        self, 
        phone: str, 
        direction: str, 
        message_type: str, 
        content: str,
        external_id: str = None
    ):
        """Log message to database"""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.phone == phone).first()
                
                if not user:
                    return
                
                # Get or create session
                db_session = db.query(DBSession).filter(
                    DBSession.phone == phone,
                    DBSession.user_id == user.id
                ).order_by(DBSession.created_at.desc()).first()
                
                if not db_session:
                    redis_session = session_manager.get_session(phone)
                    db_session = DBSession(
                        user_id=user.id,
                        phone=phone,
                        state=redis_session.get("state", "idle") if redis_session else "idle",
                        context=redis_session.get("context", {}) if redis_session else {}
                    )
                    db.add(db_session)
                    db.flush()
                
                message = Message(
                    session_id=db_session.id,
                    direction=direction,
                    message_type=message_type,
                    content=content,
                    meta_data={"external_id": external_id} if external_id else {}
                )
                
                db.add(message)
                db.commit()
                
        except Exception as e:
            logger.error("message_logging_error", phone=phone, error=str(e))


# Global message processor instance
message_processor = MessageProcessor()
