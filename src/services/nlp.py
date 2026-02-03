"""
NLP Service - Intent Classification
"""

import re
from ..settings import flows_config


class NLPService:
    """Intent classification using regex patterns"""

    def __init__(self):
        intents_config = flows_config.get("intents", {})
        self.allowed_intents = set(intents_config.get("allowed", []))
        self.intent_patterns = intents_config.get("patterns", {})

    def classify_intent(self, message: str) -> str:
        """Classify message intent using pattern matching"""
        msg = message.lower().strip()

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, msg):
                    return intent

        return "unknown"


nlp_service = NLPService()
