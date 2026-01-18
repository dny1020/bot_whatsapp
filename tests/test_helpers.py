"""
Test utilities and helpers
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.helpers import (
    normalize_phone, validate_phone, format_currency,
    generate_order_id, sanitize_input, format_menu_item
)


def test_normalize_phone():
    """Test phone number normalization"""
    assert normalize_phone("+1 (234) 567-8900") == "12345678900"
    assert normalize_phone("234-567-8900") == "2345678900"
    assert normalize_phone("2345678900") == "2345678900"


def test_validate_phone():
    """Test phone number validation"""
    assert validate_phone("1234567890") is True
    assert validate_phone("+1 234 567 8900") is True
    assert validate_phone("123") is False
    assert validate_phone("") is False


def test_format_currency():
    """Test currency formatting"""
    assert format_currency(10.5) == "$10.50"
    assert format_currency(100) == "$100.00"
    assert format_currency(0.99) == "$0.99"


def test_generate_order_id():
    """Test order ID generation"""
    order_id = generate_order_id()
    assert order_id.startswith("ORD-")
    assert len(order_id) > 10
    
    # Test uniqueness
    order_id2 = generate_order_id()
    assert order_id != order_id2


def test_sanitize_input():
    """Test input sanitization"""
    assert sanitize_input("  hello  world  ") == "hello world"
    assert sanitize_input("test<script>") == "testscript"
    assert sanitize_input("normal text") == "normal text"


def test_format_menu_item():
    """Test menu item formatting"""
    item = {
        "name": "Pizza",
        "description": "Delicious pizza",
        "price": 12.99,
        "available": True
    }
    
    formatted = format_menu_item(item)
    assert "Pizza" in formatted
    assert "$12.99" in formatted
    assert "✅" in formatted
    
    item["available"] = False
    formatted = format_menu_item(item)
    assert "❌" in formatted
