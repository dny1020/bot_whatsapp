"""
Tests básicos del ciclo de conversación
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base, User, Conversation, Message
from src.services.session import get_or_create_user, get_or_create_conversation, update_conversation_state
from src.settings import flows_config


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def db_engine():
    """Crear engine de prueba con SQLite en memoria"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Crear sesión de prueba"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# =============================================================================
# Tests de Usuario
# =============================================================================

def test_create_new_user(db_session):
    """Crear usuario nuevo"""
    phone = "+573001234567"
    
    user, is_new = get_or_create_user(phone, db_session)
    
    assert user is not None
    assert user.phone == phone
    assert is_new == True
    assert user.total_conversations == 0


def test_get_existing_user(db_session):
    """Obtener usuario existente"""
    phone = "+573001234567"
    
    # Crear primero
    user1, _ = get_or_create_user(phone, db_session)
    
    # Obtener de nuevo
    user2, is_new = get_or_create_user(phone, db_session)
    
    assert user2.id == user1.id
    assert is_new == False


# =============================================================================
# Tests de Conversación
# =============================================================================

def test_create_new_conversation(db_session):
    """Crear conversación nueva"""
    phone = "+573009876543"
    
    # Crear usuario primero
    get_or_create_user(phone, db_session)
    
    # Crear conversación
    conv = get_or_create_conversation(phone, db_session)
    
    assert conv is not None
    assert conv.phone == phone
    assert conv.status == "active"
    assert conv.state == "idle"


def test_update_conversation_state(db_session):
    """Actualizar estado de conversación"""
    phone = "+573005555555"
    
    get_or_create_user(phone, db_session)
    conv = get_or_create_conversation(phone, db_session)
    
    # Actualizar estado
    update_conversation_state(conv, "support_lvl1", db_session, {"current_flow": "support_lvl1"})
    
    db_session.refresh(conv)
    
    assert conv.state == "support_lvl1"
    assert conv.context.get("current_flow") == "support_lvl1"


# =============================================================================
# Tests de Flujos
# =============================================================================

def test_flows_config_loaded():
    """Verificar que flows.json está cargado"""
    assert flows_config is not None
    assert "flows" in flows_config
    assert "welcome" in flows_config["flows"]


def test_welcome_flow_has_buttons():
    """Verificar que welcome tiene botones"""
    welcome = flows_config["flows"]["welcome"]
    
    assert "buttons" in welcome
    assert len(welcome["buttons"]) >= 3


def test_support_has_4_levels():
    """Verificar que soporte tiene 4 niveles"""
    flows = flows_config["flows"]
    
    assert "support_lvl1" in flows
    assert "support_lvl2_conn" in flows
    assert "support_lvl3_no_service" in flows
    assert "support_lvl4_recent" in flows


def test_plans_has_4_levels():
    """Verificar que planes tiene 4 niveles"""
    flows = flows_config["flows"]
    
    assert "plans_lvl1" in flows
    assert "plans_lvl2_home" in flows
    assert "plans_lvl3_basic" in flows
    assert "plans_lvl4_contract" in flows


def test_billing_has_4_levels():
    """Verificar que facturación tiene 4 niveles"""
    flows = flows_config["flows"]
    
    assert "billing_lvl1" in flows
    assert "billing_lvl2_pay" in flows
    assert "billing_lvl3_transfer" in flows
    assert "billing_lvl4_yes" in flows


# =============================================================================
# Tests de Navegación de Flujos
# =============================================================================

def test_flow_buttons_have_valid_targets():
    """Verificar que los botones apuntan a flujos existentes"""
    flows = flows_config["flows"]
    
    for flow_id, flow_data in flows.items():
        buttons = flow_data.get("buttons", [])
        for btn in buttons:
            target_id = btn.get("id")
            assert target_id in flows, f"Botón '{btn.get('title')}' en '{flow_id}' apunta a flujo inexistente: {target_id}"
