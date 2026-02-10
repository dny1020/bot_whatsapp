"""
Inteligencia local del bot - funciones genéricas reutilizables
"""

import re
import hashlib
from datetime import datetime, timedelta
from rapidfuzz import fuzz, process
from textblob import TextBlob

from ..settings import business_config, get_logger

logger = get_logger(__name__)

# Datos cargados desde config/settings.json (editables sin tocar código)
_business = business_config.get("business", {})
_business_phone = _business.get("phone", "")


_response_cache = {}
CACHE_TTL_HOURS = 24
MAX_CACHE_SIZE = 500


def get_cached_response(question):
    """Buscar respuesta en cache"""
    key = _make_cache_key(question)
    
    if key in _response_cache:
        entry = _response_cache[key]
        if datetime.utcnow() < entry["expires"]:
            logger.info(f"Cache hit para: {question[:50]}...")
            return entry["response"]
        else:
            del _response_cache[key]
    
    return None


def cache_response(question, response):
    """Guardar respuesta en cache"""
    if len(_response_cache) >= MAX_CACHE_SIZE:
        _cleanup_cache()
    
    key = _make_cache_key(question)
    _response_cache[key] = {
        "response": response,
        "expires": datetime.utcnow() + timedelta(hours=CACHE_TTL_HOURS),
        "hits": 0
    }


def _make_cache_key(text):
    """Generar key normalizada para cache"""
    normalized = text.lower().strip()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return hashlib.md5(normalized.encode()).hexdigest()


def _cleanup_cache():
    """Limpiar entradas expiradas o menos usadas"""
    now = datetime.utcnow()
    expired = [k for k, v in _response_cache.items() if now > v["expires"]]
    for k in expired:
        del _response_cache[k]



def fuzzy_match_option(user_input, options, threshold=70):
    """
    Buscar la mejor coincidencia fuzzy para el input del usuario
    """
    if not user_input or not options:
        return None, 0
    
    user_input = user_input.lower().strip()
    
    # Buscar mejor coincidencia
    result = process.extractOne(
        user_input,
        [opt.lower() for opt in options],
        scorer=fuzz.WRatio
    )
    
    if result and result[1] >= threshold:
        # Retornar la opcion original (no lowercase)
        original_idx = [opt.lower() for opt in options].index(result[0])
        return options[original_idx], result[1]
    
    return None, 0


def correct_common_typos(text):
    """Corregir typos comunes en español"""
    corrections = {
        "soprte": "soporte",
        "tecnco": "tecnico",
        "facturacion": "facturacion",
        "pago": "pago",
        "interntet": "internet",
        "coneccion": "conexion",
        "router": "router",
        "lentoo": "lento",
        "rapdo": "rapido",
        "ayda": "ayuda",
        "problma": "problema",
        "solucion": "solucion",
    }
    
    words = text.lower().split()
    corrected = []
    
    for word in words:
        # Buscar correccion exacta o fuzzy
        if word in corrections:
            corrected.append(corrections[word])
        else:
            # Fuzzy match contra correcciones conocidas
            match, score = fuzzy_match_option(word, list(corrections.keys()), threshold=80)
            if match:
                corrected.append(corrections[match])
            else:
                corrected.append(word)
    
    return " ".join(corrected)


# Keyword responses cargadas desde config (editables por negocio)
_raw_keywords = business_config.get("keyword_responses", {})
KEYWORD_RESPONSES = {}
for pattern, response in _raw_keywords.items():
    # Reemplazar placeholders de negocio en las respuestas
    if isinstance(response, str):
        response = response.replace("{business_phone}", _business_phone)
    KEYWORD_RESPONSES[pattern] = response


def check_keyword_trigger(message):
    """Verificar si el mensaje activa una respuesta automática"""
    message_lower = message.lower().strip()

    for pattern, response in KEYWORD_RESPONSES.items():
        if re.search(pattern, message_lower, re.IGNORECASE):
            logger.info(f"Keyword trigger: {pattern}")
            return response  # None = ir a welcome

    return False


def analyze_sentiment(text):
    """
    Analizar sentimiento del mensaje
    """
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        # Detectar palabras de frustracion en español
        frustration_words = [
            "malisimo", "pesimo", "horrible", "terrible", "enojado",
            "molesto", "furioso", "harto", "cansado", "ridiculo",
            "estafa", "robo", "ladrones", "incompetentes", "inaceptable",
            "demanda", "abogado", "reclamo", "queja", "denuncia"
        ]
        
        text_lower = text.lower()
        has_frustration = any(word in text_lower for word in frustration_words)
        
        # Detectar mayusculas excesivas (gritos)
        uppercase_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        is_shouting = uppercase_ratio > 0.5 and len(text) > 10
        
        # Detectar signos de exclamacion multiples
        has_multiple_exclamation = "!!!" in text or "???" in text
        
        is_negative = polarity < -0.2
        is_frustrated = has_frustration or is_shouting or (is_negative and has_multiple_exclamation)
        needs_human = is_frustrated and (polarity < -0.5 or has_frustration)
        
        return {
            "polarity": polarity,
            "is_negative": is_negative,
            "is_frustrated": is_frustrated,
            "needs_human": needs_human
        }
    except Exception as e:
        logger.error(f"Error en sentiment analysis: {e}")
        return {
            "polarity": 0,
            "is_negative": False,
            "is_frustrated": False,
            "needs_human": False
        }


def get_empathetic_prefix(sentiment):
    """Obtener prefijo empatico basado en sentimiento"""
    if sentiment.get("needs_human"):
        return "Lamento mucho los inconvenientes. Voy a escalar su caso a un agente humano. "
    elif sentiment.get("is_frustrated"):
        return "Entiendo su frustracion y lamento los inconvenientes. "
    elif sentiment.get("is_negative"):
        return "Lamento que este teniendo problemas. "
    return ""


def extract_entities(text):
    """
    Extraer entidades del texto (telefono, email, fecha)
    
    Returns:
        dict con entidades encontradas
    """
    entities = {}
    
    # Telefono (varios formatos)
    phone_pattern = r'[\+]?[\d]{1,3}[-\s]?[\d]{3}[-\s]?[\d]{3}[-\s]?[\d]{4}'
    phones = re.findall(phone_pattern, text)
    if phones:
        entities["phone"] = phones[0]
    
    # Email
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    emails = re.findall(email_pattern, text)
    if emails:
        entities["email"] = emails[0]
    
    # Numeros de cuenta/contrato
    account_pattern = r'\b[A-Z]{0,3}\d{6,12}\b'
    accounts = re.findall(account_pattern, text)
    if accounts:
        entities["account"] = accounts[0]
    
    return entities


def extract_nickname(text):
    """
    Extraer nickname/nombre del mensaje del usuario
    """
    text = text.strip()
    
    # Patron 1: "soy [titulo] nombre" o "me llamo nombre"
    patterns = [
        r'\b(?:soy|me llamo|mi nombre es)\s+(?:el|la|ing\.|dr\.|lic\.)?\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)',
        r'\b(?:soy|me llamo)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Validar que no sea una palabra comun
            common_words = ['el', 'la', 'un', 'una', 'cliente', 'usuario', 'persona']
            if name.lower() not in common_words and len(name) >= 2:
                return name.capitalize()
    
    # Patron 2: Saludo seguido de coma y nombre "buenas, Juan"
    match = re.search(r'^(?:hola|buenas?|buenos?\s+\w+),?\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)', text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        if len(name) >= 2:
            return name.capitalize()
    
    return None


# Respuestas progresivas cargadas desde config (editables por negocio)
_raw_progressive = business_config.get("progressive_responses", {})
PROGRESSIVE_RESPONSES = {}
for topic, levels in _raw_progressive.items():
    # JSON keys son strings, convertir a int para acceso por nivel
    PROGRESSIVE_RESPONSES[topic] = {int(k): v for k, v in levels.items()}

# Patrones de detección de tema (configurables)
TOPIC_PATTERNS = business_config.get("progressive_topics", {})


def get_progressive_response(topic, interaction_count):
    """Obtener respuesta según nivel de interacción (1=detallada, 3=breve)"""
    if topic not in PROGRESSIVE_RESPONSES:
        return None

    responses = PROGRESSIVE_RESPONSES[topic]
    level = min(interaction_count, 3)

    return responses.get(level, responses.get(3))


def detect_topic_for_progressive(message):
    """Detectar tema del mensaje para respuestas progresivas"""
    message_lower = message.lower()

    for topic, keywords in TOPIC_PATTERNS.items():
        if any(kw in message_lower for kw in keywords):
            return topic

    return None


def adjust_response_length(response, user_message_length):
    """
    Ajustar longitud de respuesta segun el estilo del usuario (lenguaje espejo)
    """

    if user_message_length < 20:
        # Tomar solo la primera oracion o linea
        lines = response.split('\n')
        if lines:
            first_line = lines[0]
            if len(first_line) > 100:
                # Cortar en el primer punto
                parts = first_line.split('. ')
                if len(parts) > 1:
                    return parts[0] + '.'
            return first_line
    
    return response
