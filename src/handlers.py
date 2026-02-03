"""
Message Handlers - Main Orchestration Logic
"""

from datetime import datetime
from sqlalchemy.orm import Session as DBSession

from .settings import business_config, flows_config, get_logger
from .utils import sanitize_input
from .db import get_db_context
from .models import Conversation, Message
from .services import whatsapp_client, session_service, nlp_service, llm_service

logger = get_logger(__name__)


class MessageHandler:
    """Main message processing orchestrator"""

    async def process_message(
        self, phone: str, message: str, external_id: str | None = None
    ) -> None:
        """Process incoming WhatsApp message"""
        message = sanitize_input(message)

        with get_db_context() as db:
            user, _ = session_service.get_or_create_user(phone, db)
            conversation = session_service.get_or_create_conversation(phone, db)

            # Idempotency check
            if (
                external_id
                and db.query(Message).filter(Message.id == external_id).first()
            ):
                return

            self._log_message(conversation, "user", message, external_id, db)
            intent = nlp_service.classify_intent(message)

            # Route based on state
            if conversation.state == "idle":
                await self._handle_idle(phone, intent, db)
            elif conversation.state == "technical_support":
                await self._handle_support(phone, message, conversation, db)
            else:
                await self._send_welcome_menu(phone)

    async def _handle_idle(self, phone: str, intent: str, db: DBSession) -> None:
        """Handle message when conversation is idle"""
        if intent == "support":
            await self._start_support(phone, db)
        elif intent == "plans":
            await self._show_plans(phone)
        elif intent == "billing":
            await self._show_billing(phone)
        elif intent == "greeting":
            await self._send_welcome_menu(phone)
        else:
            await self._send_welcome_menu(phone)

    async def _handle_support(
        self, phone: str, message: str, conversation: Conversation, db: DBSession
    ) -> None:
        """Handle message in technical support flow"""
        flow = flows_config.get("flows", {}).get("technical_support", {})
        exit_commands = flow.get("exit_commands", ["salir", "cancelar", "menu"])

        if message.lower() in exit_commands:
            session_service.update_state(conversation, "idle", db)
            await self._send_welcome_menu(phone)
            return

        # Get AI response with chat history
        ctx = conversation.context or {}
        history = ctx.get("chat_history", [])

        response = await llm_service.get_response(message, history)
        self._log_message(conversation, "bot", response, None, db)

        # Update history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        session_service.update_state(
            conversation, "technical_support", db, {"chat_history": history[-6:]}
        )

        await whatsapp_client.send_text_message(phone, response)

    async def _send_welcome_menu(self, phone: str) -> None:
        """Send welcome menu with options"""
        business = business_config.get("business", {})
        flow = flows_config.get("flows", {}).get("welcome", {})

        welcome_text = flow.get("text", "").replace(
            "{business_name}", business.get("name", "nuestra empresa")
        )
        buttons = flow.get("buttons", [])
        header = flow.get("header", "Menú")

        await whatsapp_client.send_interactive_buttons(
            phone, welcome_text, buttons, header
        )

    async def _start_support(self, phone: str, db: DBSession) -> None:
        """Start technical support flow"""
        conversation = session_service.get_or_create_conversation(phone, db)
        session_service.update_state(conversation, "technical_support", db)

        flow = flows_config.get("flows", {}).get("technical_support", {})
        defaults = flows_config.get("defaults", {})
        msg = flow.get(
            "start_message",
            defaults.get(
                "fallback_support_message",
                "🔧 *Soporte Técnico*\n\nPor favor, describa su problema.",
            ),
        )

        await whatsapp_client.send_text_message(phone, msg)

    async def _show_plans(self, phone: str) -> None:
        """Show available plans"""
        flow = flows_config.get("flows", {}).get("plans", {})
        defaults = flows_config.get("defaults", {})
        msg = flow.get(
            "text",
            defaults.get(
                "fallback_plans_message", "Consulte nuestros planes disponibles."
            ),
        )

        await whatsapp_client.send_text_message(phone, msg)

    async def _show_billing(self, phone: str) -> None:
        """Show billing information"""
        flow = flows_config.get("flows", {}).get("billing", {})
        defaults = flows_config.get("defaults", {})
        msg = flow.get(
            "text",
            defaults.get("fallback_billing_message", "Información de facturación."),
        )

        await whatsapp_client.send_text_message(phone, msg)

    def _log_message(
        self,
        conversation: Conversation,
        sender: str,
        content: str,
        external_id: str | None,
        db: DBSession,
    ) -> None:
        """Log message to database"""
        msg_id = (
            external_id
            or f"bot_{int(datetime.utcnow().timestamp())}_{conversation.id[:8]}"
        )
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


message_handler = MessageHandler()
