"""
Tests minimos para validar el ciclo de conversacion y flujos
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base, User, Conversation
from src.services.session import get_or_create_user, get_or_create_conversation, update_conversation_state
from src.settings import flows_config


# Setup: base de datos en memoria para tests
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# Tests de usuarios
def test_create_new_user(db_session):
    user, created = get_or_create_user("+1234567890", db_session)
    assert created is True
    assert user.phone == "+1234567890"


def test_get_existing_user(db_session):
    get_or_create_user("+1234567890", db_session)
    user, created = get_or_create_user("+1234567890", db_session)
    assert created is False
    assert user.phone == "+1234567890"


# Tests de conversaciones
def test_create_new_conversation(db_session):
    get_or_create_user("+1234567890", db_session)
    conv = get_or_create_conversation("+1234567890", db_session)
    assert conv is not None
    assert conv.phone == "+1234567890"


def test_update_conversation_state(db_session):
    get_or_create_user("+1234567890", db_session)
    conv = get_or_create_conversation("+1234567890", db_session)
    update_conversation_state(conv, "active", db_session, {"current_flow": "support_lvl1"})
    assert conv.state == "active"
    assert conv.context.get("current_flow") == "support_lvl1"


# Tests de flows_config
def test_flows_config_loaded():
    assert flows_config is not None
    assert "flows" in flows_config
    assert "welcome" in flows_config["flows"]


def test_welcome_flow_has_buttons():
    welcome = flows_config["flows"]["welcome"]
    assert "buttons" in welcome
    assert len(welcome["buttons"]) >= 3


def test_support_has_4_levels():
    flows = flows_config["flows"]
    assert "support_lvl1" in flows
    assert "support_lvl2_conn" in flows
    assert "support_lvl3_no_service" in flows
    assert "support_lvl4_recent" in flows


def test_plans_has_4_levels():
    flows = flows_config["flows"]
    assert "plans_lvl1" in flows
    assert "plans_lvl2_home" in flows
    assert "plans_lvl3_basic" in flows
    assert "plans_lvl4_contract" in flows


def test_billing_has_4_levels():
    flows = flows_config["flows"]
    assert "billing_lvl1" in flows
    assert "billing_lvl2_pay" in flows
    assert "billing_lvl3_transfer" in flows
    assert "billing_lvl4_yes" in flows


def test_flow_buttons_have_valid_targets():
    """Verificar que todos los botones apuntan a flujos existentes"""
    flows = flows_config["flows"]
    missing = []
    
    for flow_id, flow_data in flows.items():
        buttons = flow_data.get("buttons", [])
        for btn in buttons:
            target_id = btn.get("id")
            if target_id and target_id not in flows:
                missing.append(f"{flow_id} -> {target_id}")
    
    assert len(missing) == 0, f"Botones con targets invalidos: {missing}"
