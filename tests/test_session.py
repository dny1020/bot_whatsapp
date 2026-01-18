"""
Test session manager
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_session_creation():
    """Test session creation"""
    from backend.session_manager import SessionManager
    
    manager = SessionManager()
    phone = "1234567890"
    
    # Create session
    session = manager.create_session(phone, "idle")
    
    assert session["phone"] == phone
    assert session["state"] == "idle"
    assert "context" in session


def test_session_state_update():
    """Test session state updates"""
    from backend.session_manager import SessionManager
    
    manager = SessionManager()
    phone = "1234567890"
    
    manager.create_session(phone, "idle")
    manager.update_state(phone, "ordering", {"test": "value"})
    
    session = manager.get_session(phone)
    assert session["state"] == "ordering"
    assert session["context"]["test"] == "value"


def test_session_context():
    """Test session context management"""
    from backend.session_manager import SessionManager
    
    manager = SessionManager()
    phone = "1234567890"
    
    manager.create_session(phone)
    manager.set_context(phone, "order_total", 25.50)
    
    value = manager.get_context(phone, "order_total")
    assert value == 25.50
    
    manager.clear_context(phone, "order_total")
    value = manager.get_context(phone, "order_total")
    assert value is None
