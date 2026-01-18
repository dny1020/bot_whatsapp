"""
NLP Service - Natural Language Processing utilities
Intent classification, entity extraction, sentiment analysis
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)


class IntentClassifier:
    """Rule-based intent classifier with keyword matching"""
    
    def __init__(self):
        self.intent_patterns = {
            "greeting": [
                r"\b(hola|buenos días|buenas tardes|buenas noches|hey|hi|hello|saludos)\b",
                r"\b(qué tal|cómo estás|cómo está)\b"
            ],
            "show_menu": [
                r"\b(menú|menu|carta|opciones|productos|qué tienen|que tienen)\b",
                r"\b(ver.*menú|mostrar.*menú|quiero ver)\b"
            ],
            "order": [
                r"\b(pedido|pedir|ordenar|orden|comprar|quiero)\b",
                r"\b(hacer.*pedido|nueva.*orden)\b"
            ],
            "track_order": [
                r"\b(estado|rastrear|seguimiento|dónde.*pedido|donde.*pedido)\b",
                r"\b(mi.*pedido|mi.*orden|número.*orden)\b"
            ],
            "hours": [
                r"\b(horario|hora|abierto|cerrado|atienden|atención)\b",
                r"\b(qué.*hora|a qué hora|hasta.*hora)\b"
            ],
            "delivery": [
                r"\b(delivery|entrega|envío|envio|domicilio|reparto)\b",
                r"\b(costo.*entrega|precio.*delivery|zona.*entrega)\b"
            ],
            "payment": [
                r"\b(pago|pagar|efectivo|tarjeta|transferencia)\b",
                r"\b(método.*pago|forma.*pago|cómo.*pagar|como.*pagar)\b"
            ],
            "cancel": [
                r"\b(cancelar|anular|borrar|eliminar|quitar)\b",
                r"\b(no quiero|ya no|cambié.*mente|cambie.*mente)\b"
            ],
            "help": [
                r"\b(ayuda|help|soporte|asistencia|información|informacion)\b",
                r"\b(cómo.*funciona|como.*funciona|necesito.*ayuda)\b"
            ],
            "thanks": [
                r"\b(gracias|thank|agradezco|muchas gracias)\b"
            ],
            "farewell": [
                r"\b(adiós|adios|chao|hasta luego|nos vemos|bye)\b"
            ],
            "complaint": [
                r"\b(queja|reclamo|problema|malo|terrible|pésimo|pesimo)\b",
                r"\b(no.*llegó|no.*llego|nunca.*llegó|demora)\b"
            ],
            "affirmative": [
                r"\b(sí|si|yes|ok|okay|vale|dale|perfecto|claro|correcto|confirmar|confirmo)\b"
            ],
            "negative": [
                r"\b(no|nop|nope|nunca|jamás|jamas|negativo)\b"
            ]
        }
    
    def classify(self, message: str) -> str:
        """Classify intent from message"""
        message_lower = message.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    logger.info("intent_classified", intent=intent, message=message[:50])
                    return intent
        
        return "other"
    
    def get_confidence_scores(self, message: str) -> Dict[str, float]:
        """Get confidence scores for all intents"""
        message_lower = message.lower().strip()
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            
            if score > 0:
                scores[intent] = min(score / len(patterns), 1.0)
        
        return scores


class EntityExtractor:
    """Extract entities from text"""
    
    def __init__(self):
        self.patterns = {
            "phone": r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "currency": r"\$?\s?\d+(?:[.,]\d{2})?",
            "number": r"\b\d+\b",
            "order_id": r"\b(?:ORD|ORDER)[-_]?\d+[-_]?[A-Z0-9]+\b"
        }
    
    def extract(self, message: str) -> Dict[str, Any]:
        """Extract all entities from message"""
        entities = {}
        
        # Extract phone
        phone_match = re.search(self.patterns["phone"], message)
        if phone_match:
            entities["phone"] = phone_match.group()
        
        # Extract email
        email_match = re.search(self.patterns["email"], message)
        if email_match:
            entities["email"] = email_match.group()
        
        # Extract currency amounts
        currency_matches = re.findall(self.patterns["currency"], message)
        if currency_matches:
            entities["amounts"] = currency_matches
        
        # Extract numbers
        number_matches = re.findall(self.patterns["number"], message)
        if number_matches:
            entities["numbers"] = [int(n) for n in number_matches]
        
        # Extract order ID
        order_match = re.search(self.patterns["order_id"], message, re.IGNORECASE)
        if order_match:
            entities["order_id"] = order_match.group()
        
        # Extract address indicators
        address_keywords = ["calle", "avenida", "av.", "jirón", "jr.", "pasaje", 
                           "mz.", "lote", "casa", "dpto", "piso"]
        message_lower = message.lower()
        
        for keyword in address_keywords:
            if keyword in message_lower:
                entities["has_address"] = True
                break
        
        logger.debug("entities_extracted", count=len(entities))
        return entities
    
    def extract_quantity(self, message: str) -> Optional[int]:
        """Extract quantity from message"""
        # Look for patterns like "2 pizzas", "quiero 3", etc.
        patterns = [
            r"(\d+)\s*(?:unidades?|piezas?|productos?)?",
            r"(?:quiero|necesito|dame)\s*(\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None


class SentimentAnalyzer:
    """Simple sentiment analysis"""
    
    def __init__(self):
        self.positive_words = [
            "bueno", "excelente", "genial", "perfecto", "gracias", "feliz",
            "contento", "me gusta", "increíble", "fantástico", "rico"
        ]
        
        self.negative_words = [
            "malo", "terrible", "pésimo", "horrible", "nunca", "problema",
            "queja", "reclamo", "demora", "tardó", "frío", "frio", "mal"
        ]
    
    def analyze(self, message: str) -> Dict[str, Any]:
        """Analyze sentiment of message"""
        message_lower = message.lower()
        
        positive_count = sum(1 for word in self.positive_words if word in message_lower)
        negative_count = sum(1 for word in self.negative_words if word in message_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(positive_count / (positive_count + negative_count), 1.0)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = min(negative_count / (positive_count + negative_count), 1.0)
        else:
            sentiment = "neutral"
            score = 0.5
        
        return {
            "sentiment": sentiment,
            "score": score,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count
        }


class NLPService:
    """Main NLP service combining all processors"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        logger.info("nlp_service_initialized")
    
    def process(self, message: str) -> Dict[str, Any]:
        """Process message and extract all NLP features"""
        result = {
            "intent": self.intent_classifier.classify(message),
            "intent_scores": self.intent_classifier.get_confidence_scores(message),
            "entities": self.entity_extractor.extract(message),
            "sentiment": self.sentiment_analyzer.analyze(message),
            "quantity": self.entity_extractor.extract_quantity(message),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        logger.info("nlp_processed", 
                   intent=result["intent"],
                   sentiment=result["sentiment"]["sentiment"],
                   entities_count=len(result["entities"]))
        
        return result
    
    def should_escalate_to_human(self, nlp_result: Dict[str, Any]) -> bool:
        """Determine if conversation should escalate to human"""
        # Escalate on negative sentiment
        if nlp_result["sentiment"]["sentiment"] == "negative":
            if nlp_result["sentiment"]["score"] > 0.7:
                return True
        
        # Escalate on complaint intent
        if nlp_result["intent"] == "complaint":
            return True
        
        # Escalate if no clear intent
        if nlp_result["intent"] == "other":
            if not nlp_result["intent_scores"]:
                return True
        
        return False


# Global NLP service instance
nlp_service = NLPService()
