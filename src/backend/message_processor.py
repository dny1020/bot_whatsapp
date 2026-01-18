"""
Message processor and bot logic
"""
from typing import Dict, Any, Optional
from datetime import datetime
from .session_manager import session_manager
from .whatsapp_client import whatsapp_client
from .database import get_db_context
from .models import User, Order, Message, Session as DBSession
from ..utils.helpers import (
    normalize_phone, is_business_open, get_business_hours_message,
    calculate_delivery_fee, generate_order_id, format_menu_item,
    format_order_summary, extract_address_from_message, sanitize_input
)
from ..utils.config import business_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MessageProcessor:
    """Process incoming messages and manage conversation flow"""
    
    def __init__(self):
        self.commands = {
            "menu": self.show_menu,
            "menú": self.show_menu,
            "pedido": self.start_order,
            "orden": self.start_order,
            "horario": self.show_hours,
            "horarios": self.show_hours,
            "ayuda": self.show_help,
            "help": self.show_help,
            "cancelar": self.cancel_order,
            "estado": self.check_order_status,
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
            elif state == "browsing_menu":
                await self.handle_menu_browsing(phone, message)
            elif state == "adding_items":
                await self.handle_adding_items(phone, message)
            elif state == "awaiting_address":
                await self.handle_address_input(phone, message)
            elif state == "awaiting_payment":
                await self.handle_payment_selection(phone, message)
            elif state == "confirming_order":
                await self.handle_order_confirmation(phone, message)
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
            {"id": "btn_menu", "title": "🍔 Ver Menú"},
            {"id": "btn_order", "title": "🛒 Hacer Pedido"},
            {"id": "btn_help", "title": "ℹ️ Ayuda"}
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
        
        if not is_business_open():
            response = f"¡Hola! Gracias por contactar a *{business.get('name')}* 🏪\n\n"
            response += "Actualmente estamos cerrados. 😴\n\n"
            response += get_business_hours_message()
            response += "\n\n¡Te esperamos pronto!"
            await whatsapp_client.send_text_message(phone, response)
            return
        
        welcome = f"¡Hola! Bienvenido a *{business.get('name')}* 🏪\n\n"
        welcome += f"{business.get('description')}\n\n"
        welcome += "¿En qué puedo ayudarte hoy?\n\n"
        welcome += "Comandos disponibles:\n"
        welcome += "• *menu* - Ver nuestro menú\n"
        welcome += "• *pedido* - Hacer un pedido\n"
        welcome += "• *horario* - Ver horarios\n"
        welcome += "• *ayuda* - Más información"
        
        await whatsapp_client.send_text_message(phone, welcome)
    
    async def show_menu(self, phone: str):
        """Show menu to user"""
        if not is_business_open():
            await whatsapp_client.send_text_message(
                phone,
                "Lo siento, estamos cerrados en este momento. 😴\n\n" + get_business_hours_message()
            )
            return
        
        menu = business_config.get("menu", {})
        categories = menu.get("categories", [])
        
        if not categories:
            await whatsapp_client.send_text_message(
                phone,
                "Lo siento, el menú no está disponible en este momento."
            )
            return
        
        # Build menu message
        menu_text = "📋 *NUESTRO MENÚ*\n\n"
        
        for category in categories:
            menu_text += f"🔹 *{category['name']}*\n\n"
            
            for item in category.get("items", []):
                menu_text += format_menu_item(item) + "\n\n"
        
        menu_text += "\n💬 Escribe *pedido* para hacer tu orden"
        
        await whatsapp_client.send_text_message(phone, menu_text)
        session_manager.update_state(phone, "browsing_menu")
    
    async def start_order(self, phone: str):
        """Start order process"""
        if not is_business_open():
            await whatsapp_client.send_text_message(
                phone,
                "Lo siento, estamos cerrados. No podemos tomar pedidos en este momento.\n\n" +
                get_business_hours_message()
            )
            return
        
        # Initialize order context
        session_manager.update_state(phone, "adding_items", {
            "order_items": [],
            "order_total": 0.0
        })
        
        response = "🛒 *Perfecto! Vamos a hacer tu pedido*\n\n"
        response += "Por favor, dime qué deseas ordenar.\n"
        response += "Puedes escribir el nombre o número del producto.\n\n"
        response += "Escribe *menu* si necesitas ver las opciones nuevamente.\n"
        response += "Escribe *listo* cuando termines de agregar productos."
        
        await whatsapp_client.send_text_message(phone, response)
    
    async def handle_menu_browsing(self, phone: str, message: str):
        """Handle menu browsing state"""
        if message.lower() == "pedido" or message.lower() == "orden":
            await self.start_order(phone)
        else:
            await self.handle_idle_state(phone, message)
    
    async def handle_adding_items(self, phone: str, message: str):
        """Handle adding items to order"""
        message_lower = message.lower().strip()
        
        if message_lower in ["listo", "terminar", "finalizar", "ya"]:
            await self.proceed_to_address(phone)
            return
        
        if message_lower in ["cancelar", "cancel"]:
            await self.cancel_order(phone)
            return
        
        # Try to find and add item
        menu = business_config.get("menu", {})
        found_item = None
        
        for category in menu.get("categories", []):
            for item in category.get("items", []):
                if message_lower in item["name"].lower():
                    found_item = item
                    break
            if found_item:
                break
        
        if found_item:
            # Add item to order
            context = session_manager.get_context(phone)
            order_items = context.get("order_items", [])
            order_total = context.get("order_total", 0.0)
            
            order_items.append({
                "id": found_item.get("id"),
                "name": found_item["name"],
                "price": found_item["price"],
                "quantity": 1
            })
            
            order_total += found_item["price"]
            
            session_manager.set_context(phone, "order_items", order_items)
            session_manager.set_context(phone, "order_total", order_total)
            
            response = f"✅ *{found_item['name']}* agregado a tu pedido\n"
            response += f"Precio: ${found_item['price']:.2f}\n\n"
            response += f"Total actual: ${order_total:.2f}\n\n"
            response += "¿Deseas agregar algo más? O escribe *listo* para continuar."
            
            await whatsapp_client.send_text_message(phone, response)
        else:
            response = "❌ No encontré ese producto en nuestro menú.\n\n"
            response += "Por favor, intenta con otro nombre o escribe *menu* para ver las opciones."
            await whatsapp_client.send_text_message(phone, response)
    
    async def proceed_to_address(self, phone: str):
        """Proceed to address collection"""
        context = session_manager.get_context(phone)
        order_items = context.get("order_items", [])
        
        if not order_items:
            await whatsapp_client.send_text_message(
                phone,
                "❌ Tu pedido está vacío. Por favor, agrega productos primero."
            )
            return
        
        session_manager.update_state(phone, "awaiting_address")
        
        response = "📍 *Perfecto! Ahora necesito tu dirección de entrega*\n\n"
        response += "Por favor, envíame tu dirección completa incluyendo:\n"
        response += "• Calle y número\n"
        response += "• Referencias importantes\n"
        response += "• Distrito/Zona"
        
        await whatsapp_client.send_text_message(phone, response)
    
    async def handle_address_input(self, phone: str, message: str):
        """Handle address input"""
        address = extract_address_from_message(message)
        
        if not address:
            await whatsapp_client.send_text_message(
                phone,
                "❌ Por favor, proporciona una dirección válida con calle, número y referencias."
            )
            return
        
        session_manager.set_context(phone, "delivery_address", address)
        session_manager.update_state(phone, "awaiting_payment")
        
        # Show payment options
        payment_methods = business_config.get("payment_methods", [])
        enabled_methods = [m for m in payment_methods if m.get("enabled", True)]
        
        response = "✅ Dirección registrada\n\n"
        response += "💳 *Selecciona tu método de pago:*\n\n"
        
        for idx, method in enumerate(enabled_methods, 1):
            response += f"{idx}. {method['name']}\n"
        
        response += "\nResponde con el número de tu preferencia."
        
        await whatsapp_client.send_text_message(phone, response)
    
    async def handle_payment_selection(self, phone: str, message: str):
        """Handle payment method selection"""
        payment_methods = business_config.get("payment_methods", [])
        enabled_methods = [m for m in payment_methods if m.get("enabled", True)]
        
        try:
            selection = int(message.strip())
            if 1 <= selection <= len(enabled_methods):
                selected_method = enabled_methods[selection - 1]
                session_manager.set_context(phone, "payment_method", selected_method["id"])
                await self.show_order_confirmation(phone)
            else:
                await whatsapp_client.send_text_message(
                    phone,
                    "❌ Selección inválida. Por favor, elige un número válido."
                )
        except ValueError:
            await whatsapp_client.send_text_message(
                phone,
                "❌ Por favor, responde con el número del método de pago."
            )
    
    async def show_order_confirmation(self, phone: str):
        """Show order confirmation"""
        context = session_manager.get_context(phone)
        
        order_data = {
            "items": context.get("order_items", []),
            "total": context.get("order_total", 0.0),
            "delivery_fee": calculate_delivery_fee(),
            "delivery_address": context.get("delivery_address"),
            "payment_method": context.get("payment_method")
        }
        
        summary = format_order_summary(order_data)
        
        payment_methods = {m["id"]: m["name"] for m in business_config.get("payment_methods", [])}
        payment_name = payment_methods.get(order_data["payment_method"], "No especificado")
        
        confirmation = summary + "\n\n"
        confirmation += f"📍 *Dirección:* {order_data['delivery_address']}\n"
        confirmation += f"💳 *Pago:* {payment_name}\n\n"
        confirmation += "⏱ *Tiempo estimado:* 30-45 minutos\n\n"
        confirmation += "¿Confirmas tu pedido?\n"
        confirmation += "Responde *SI* para confirmar o *NO* para cancelar"
        
        await whatsapp_client.send_text_message(phone, confirmation)
        session_manager.update_state(phone, "confirming_order")
    
    async def handle_order_confirmation(self, phone: str, message: str):
        """Handle order confirmation"""
        message_lower = message.lower().strip()
        
        if message_lower in ["si", "sí", "yes", "confirmar", "ok"]:
            await self.confirm_order(phone)
        elif message_lower in ["no", "cancelar", "cancel"]:
            await self.cancel_order(phone)
        else:
            await whatsapp_client.send_text_message(
                phone,
                "Por favor, responde *SI* para confirmar o *NO* para cancelar."
            )
    
    async def confirm_order(self, phone: str):
        """Confirm and save order"""
        try:
            context = session_manager.get_context(phone)
            order_id = generate_order_id()
            
            order_data = {
                "order_id": order_id,
                "items": context.get("order_items", []),
                "subtotal": context.get("order_total", 0.0),
                "delivery_fee": calculate_delivery_fee(),
                "total": context.get("order_total", 0.0) + calculate_delivery_fee(),
                "delivery_address": context.get("delivery_address"),
                "payment_method": context.get("payment_method"),
                "status": "confirmed",
                "confirmed_at": datetime.utcnow()
            }
            
            # Save to database
            with get_db_context() as db:
                user = db.query(User).filter(User.phone == phone).first()
                
                order = Order(
                    order_id=order_data["order_id"],
                    user_id=user.id,
                    items=order_data["items"],
                    subtotal=order_data["subtotal"],
                    delivery_fee=order_data["delivery_fee"],
                    total=order_data["total"],
                    delivery_address=order_data["delivery_address"],
                    payment_method=order_data["payment_method"],
                    status="confirmed",
                    confirmed_at=order_data["confirmed_at"]
                )
                
                db.add(order)
                db.commit()
            
            # Send confirmation
            response = f"✅ *¡Pedido confirmado!*\n\n"
            response += f"🔖 Número de orden: *{order_id}*\n\n"
            response += "Tu pedido está siendo preparado. 👨‍🍳\n"
            response += "Te notificaremos cuando esté en camino. 🚚\n\n"
            response += "¡Gracias por tu preferencia!"
            
            await whatsapp_client.send_text_message(phone, response)
            
            # Reset session
            session_manager.update_state(phone, "idle", {})
            session_manager.clear_context(phone)
            
            logger.info("order_confirmed", phone=phone, order_id=order_id)
            
        except Exception as e:
            logger.error("order_confirmation_error", phone=phone, error=str(e))
            await whatsapp_client.send_text_message(
                phone,
                "❌ Hubo un error confirmando tu pedido. Por favor, intenta de nuevo."
            )
    
    async def cancel_order(self, phone: str):
        """Cancel current order"""
        session_manager.update_state(phone, "idle")
        session_manager.clear_context(phone)
        
        await whatsapp_client.send_text_message(
            phone,
            "❌ Pedido cancelado. Si deseas hacer uno nuevo, escribe *pedido*."
        )
    
    async def show_hours(self, phone: str):
        """Show business hours"""
        hours_message = get_business_hours_message()
        await whatsapp_client.send_text_message(phone, hours_message)
    
    async def show_help(self, phone: str):
        """Show help message"""
        business = business_config.get("business", {})
        
        help_text = f"ℹ️ *Ayuda - {business.get('name')}*\n\n"
        help_text += "*Comandos disponibles:*\n\n"
        help_text += "• *menu* - Ver nuestro menú completo\n"
        help_text += "• *pedido* - Iniciar un nuevo pedido\n"
        help_text += "• *horario* - Ver horarios de atención\n"
        help_text += "• *estado* - Consultar estado de tu pedido\n"
        help_text += "• *cancelar* - Cancelar pedido actual\n"
        help_text += "• *ayuda* - Mostrar esta ayuda\n\n"
        help_text += f"📞 Contacto: {business.get('phone', 'N/A')}\n"
        help_text += f"📧 Email: {business.get('email', 'N/A')}"
        
        await whatsapp_client.send_text_message(phone, help_text)
    
    async def check_order_status(self, phone: str):
        """Check order status"""
        try:
            with get_db_context() as db:
                user = db.query(User).filter(User.phone == phone).first()
                
                if not user:
                    await whatsapp_client.send_text_message(
                        phone,
                        "No encontramos pedidos asociados a tu número."
                    )
                    return
                
                # Get latest order
                order = db.query(Order).filter(
                    Order.user_id == user.id,
                    Order.status != "cancelled"
                ).order_by(Order.created_at.desc()).first()
                
                if not order:
                    await whatsapp_client.send_text_message(
                        phone,
                        "No tienes pedidos activos en este momento."
                    )
                    return
                
                status_emoji = {
                    "pending": "⏳",
                    "confirmed": "✅",
                    "preparing": "👨‍🍳",
                    "delivering": "🚚",
                    "delivered": "✅",
                    "cancelled": "❌"
                }
                
                status_text = {
                    "pending": "Pendiente",
                    "confirmed": "Confirmado",
                    "preparing": "En preparación",
                    "delivering": "En camino",
                    "delivered": "Entregado",
                    "cancelled": "Cancelado"
                }
                
                emoji = status_emoji.get(order.status, "📦")
                status = status_text.get(order.status, order.status)
                
                response = f"{emoji} *Estado de tu pedido*\n\n"
                response += f"🔖 Orden: *{order.order_id}*\n"
                response += f"📊 Estado: *{status}*\n"
                response += f"💰 Total: ${order.total:.2f}\n"
                response += f"📍 Dirección: {order.delivery_address}\n"
                
                await whatsapp_client.send_text_message(phone, response)
                
        except Exception as e:
            logger.error("check_status_error", phone=phone, error=str(e))
            await whatsapp_client.send_text_message(
                phone,
                "❌ Error consultando el estado. Por favor, intenta más tarde."
            )
    
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
                    metadata={"external_id": external_id} if external_id else {}
                )
                
                db.add(message)
                db.commit()
                
        except Exception as e:
            logger.error("message_logging_error", phone=phone, error=str(e))


# Global message processor instance
message_processor = MessageProcessor()
