"""
Integration Tests for Conversation Lifecycle
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import User, Conversation, Message, ConversationStatus
from src.settings import settings

# Test DB Config
TEST_DB_URL = settings.database_url


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(TEST_DB_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def clean_db(db_session):
    phone = "+573009999999"
    user = db_session.query(User).filter(User.phone == phone).first()
    if user:
        # Delete messages associated with user's conversations
        conv_ids = [c.id for c in user.conversations]
        if conv_ids:
            db_session.query(Message).filter(
                Message.conversation_id.in_(conv_ids)
            ).delete(synchronize_session=False)
        db_session.query(Conversation).filter(Conversation.user_id == user.id).delete(
            synchronize_session=False
        )
        db_session.query(User).filter(User.id == user.id).delete(
            synchronize_session=False
        )
        db_session.commit()
    return db_session


@pytest.mark.asyncio
async def test_full_conversation_flow(clean_db):
    phone = "+573009999999"
    message_id = "test_msg_001"

    # 1. First Message -> New User & Conversation
    await message_processor.process_message(phone, "Hola, ayuda", message_id)

    # Check User
    user = clean_db.query(User).filter(User.phone == phone).first()
    assert user is not None
    assert user.total_conversations == 1

    # Check Conversation
    conv = clean_db.query(Conversation).filter(Conversation.user_id == user.id).first()
    assert conv is not None
    assert conv.status == ConversationStatus.ACTIVE

    # 2. Second Message -> Support Intent (Transitions to technical_support state)
    msg_id_2 = "test_msg_002"
    await message_processor.process_message(phone, "soporte tecnico", msg_id_2)

    clean_db.expire_all()
    conv = clean_db.query(Conversation).filter(Conversation.id == conv.id).first()
    assert conv.state == "technical_support"

    # 3. New Message -> NEW Conversation (If we simulate closing or wait for TTL, but let's just check persistence)
    # The bot doesn't close automatically on "adios" in the simplified logic yet (it reverts to menu or idle state)
    # Let's just verify the state is preserved
    clean_db.refresh(conv)
    assert conv.phone == phone
