"""
Integration Tests for Conversation Lifecycle
Verifies:
1. User creation/retrieval
2. Conversation creation and persistence
3. Message logging
4. Conversation closure logic
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backend.models import Base, User, Conversation, Message, ConversationStatus
from src.backend.session_manager import session_manager
from src.backend.user_service import user_service
from src.backend.message_processor import message_processor
from src.utils.config import settings

# Test DB Config (Use main DB for now, or test DB if configured)
TEST_DB_URL = settings.database_url

@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(TEST_DB_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Setup
    # Base.metadata.create_all(bind=engine) # Assume exists or init_db run
    
    db = TestingSessionLocal()
    yield db
    db.close()
    
    # Teardown? Be careful with prod DB.
    # For now, we trust reset_db.py ran before.

@pytest.fixture
def clean_db(db_session):
    # Clean up specific test data before/after
    phone = "+573009999999"
    user = db_session.query(User).filter(User.phone == phone).first()
    if user:
        db_session.query(Message).filter(Message.conversation.has(user_id=user.id)).delete(synchronize_session=False)
        db_session.query(Conversation).filter(Conversation.user_id == user.id).delete(synchronize_session=False)
        db_session.query(User).filter(User.id == user.id).delete(synchronize_session=False)
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
    assert conv.message_count >= 1 # Inbound + Welcome
    
    # Check Message Log
    msgs = clean_db.query(Message).filter(Message.conversation_id == conv.id).all()
    assert len(msgs) >= 1
    
    # 2. Second Message -> Same Conversation
    msg_id_2 = "test_msg_002"
    await message_processor.process_message(phone, "tengo un problema", msg_id_2)
    
    clean_db.refresh(conv)
    assert conv.message_count >= 3 # Previous + Inbound + Response
    assert conv.status == ConversationStatus.TECHNICAL_SUPPORT # Should be support intent?
    # Wait, intent might be "support" -> updates state
    # Let's verify state
    # Note: process_message commits, so we refresh
    
    # 3. Closure Message
    msg_id_3 = "test_msg_003"
    await message_processor.process_message(phone, "gracias, adiós", msg_id_3)
    
    clean_db.expire_all()
    conv = clean_db.query(Conversation).filter(Conversation.id == conv.id).first()
    assert conv.status == ConversationStatus.CLOSED
    assert conv.close_reason == "user_farewell"
    
    # 4. New Message -> NEW Conversation
    msg_id_4 = "test_msg_004"
    await message_processor.process_message(phone, "Hola de nuevo", msg_id_4)
    
    new_conv = clean_db.query(Conversation).filter(
        Conversation.user_id == user.id,
        Conversation.status == ConversationStatus.ACTIVE
    ).first()
    
    assert new_conv is not None
    assert new_conv.id != conv.id
