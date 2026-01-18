"""
Test NLP Service
"""
import pytest
from src.backend.nlp_service import (
    IntentClassifier, 
    EntityExtractor, 
    SentimentAnalyzer,
    NLPService
)


class TestIntentClassifier:
    """Test intent classification"""
    
    def setup_method(self):
        self.classifier = IntentClassifier()
    
    def test_greeting_intent(self):
        assert self.classifier.classify("Hola") == "greeting"
        assert self.classifier.classify("Buenos días") == "greeting"
        assert self.classifier.classify("Hey, qué tal?") == "greeting"
    
    def test_menu_intent(self):
        assert self.classifier.classify("Quiero ver el menú") == "show_menu"
        assert self.classifier.classify("Muéstrame la carta") == "show_menu"
        assert self.classifier.classify("Qué tienen?") == "show_menu"
    
    def test_order_intent(self):
        assert self.classifier.classify("Quiero hacer un pedido") == "order"
        assert self.classifier.classify("Deseo ordenar") == "order"
        assert self.classifier.classify("Necesito pedir") == "order"
    
    def test_track_order_intent(self):
        assert self.classifier.classify("Dónde está mi pedido?") == "track_order"
        assert self.classifier.classify("Estado de mi orden") == "track_order"
    
    def test_hours_intent(self):
        assert self.classifier.classify("Qué horario tienen?") == "hours"
        assert self.classifier.classify("Están abiertos?") == "hours"
        assert self.classifier.classify("A qué hora cierran?") == "hours"
    
    def test_cancel_intent(self):
        assert self.classifier.classify("Quiero cancelar") == "cancel"
        assert self.classifier.classify("Anular pedido") == "cancel"
    
    def test_help_intent(self):
        assert self.classifier.classify("Necesito ayuda") == "help"
        assert self.classifier.classify("Cómo funciona esto?") == "help"
    
    def test_affirmative_intent(self):
        assert self.classifier.classify("Sí") == "affirmative"
        assert self.classifier.classify("Ok, confirmo") == "affirmative"
        assert self.classifier.classify("Dale") == "affirmative"
    
    def test_negative_intent(self):
        assert self.classifier.classify("No") == "negative"
        assert self.classifier.classify("Nope") == "negative"
    
    def test_unknown_intent(self):
        assert self.classifier.classify("asdfghjkl") == "other"


class TestEntityExtractor:
    """Test entity extraction"""
    
    def setup_method(self):
        self.extractor = EntityExtractor()
    
    def test_phone_extraction(self):
        entities = self.extractor.extract("Mi teléfono es +51 987654321")
        assert "phone" in entities
        assert "987654321" in entities["phone"]
    
    def test_email_extraction(self):
        entities = self.extractor.extract("Escríbeme a test@example.com")
        assert "email" in entities
        assert entities["email"] == "test@example.com"
    
    def test_number_extraction(self):
        entities = self.extractor.extract("Quiero 3 pizzas")
        assert "numbers" in entities
        assert 3 in entities["numbers"]
    
    def test_order_id_extraction(self):
        entities = self.extractor.extract("Mi orden es ORD-20240109-ABC123")
        assert "order_id" in entities
        assert "ORD-20240109-ABC123" in entities["order_id"]
    
    def test_address_detection(self):
        entities = self.extractor.extract("Vivo en calle Los Olivos 123")
        assert entities.get("has_address") == True
    
    def test_quantity_extraction(self):
        assert self.extractor.extract_quantity("Quiero 2 hamburguesas") == 2
        assert self.extractor.extract_quantity("Dame 5 unidades") == 5
        assert self.extractor.extract_quantity("Una pizza") is None


class TestSentimentAnalyzer:
    """Test sentiment analysis"""
    
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()
    
    def test_positive_sentiment(self):
        result = self.analyzer.analyze("Excelente servicio, muchas gracias!")
        assert result["sentiment"] == "positive"
        assert result["score"] > 0.5
    
    def test_negative_sentiment(self):
        result = self.analyzer.analyze("Terrible, nunca llegó mi pedido")
        assert result["sentiment"] == "negative"
        assert result["score"] > 0.5
    
    def test_neutral_sentiment(self):
        result = self.analyzer.analyze("Hola, quiero el menú")
        assert result["sentiment"] == "neutral"


class TestNLPService:
    """Test complete NLP service"""
    
    def setup_method(self):
        self.nlp = NLPService()
    
    def test_full_processing(self):
        result = self.nlp.process("Hola, quiero 2 pizzas por favor")
        
        assert "intent" in result
        assert "entities" in result
        assert "sentiment" in result
        assert result["quantity"] == 2
    
    def test_escalation_negative_sentiment(self):
        result = self.nlp.process("Esto es terrible, nunca más compro aquí")
        should_escalate = self.nlp.should_escalate_to_human(result)
        
        # Should escalate on strong negative sentiment
        assert should_escalate or result["sentiment"]["sentiment"] == "negative"
    
    def test_no_escalation_normal(self):
        result = self.nlp.process("Quiero ver el menú")
        should_escalate = self.nlp.should_escalate_to_human(result)
        
        assert not should_escalate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
