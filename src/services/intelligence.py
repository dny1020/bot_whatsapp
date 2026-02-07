"""
Inteligencia local - Features ligeros sin LLM
- Fuzzy matching para typos
- Cache de respuestas LLM
- Keyword triggers para FAQs
- Sentiment analysis
"""

import re
import hashlib
from datetime import datetime, timedelta
from rapidfuzz import fuzz, process
from textblob import TextBlob

from ..settings import get_logger

logger = get_logger(__name__)


# =============================================================================
# Cache de respuestas LLM
# =============================================================================

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


# =============================================================================
# Fuzzy Matching para typos
# =============================================================================

def fuzzy_match_option(user_input, options, threshold=70):
    """
    Buscar la mejor coincidencia fuzzy para el input del usuario
    
    Args:
        user_input: texto del usuario
        options: lista de opciones validas (ej: titulos de botones)
        threshold: minimo score para considerar match (0-100)
    
    Returns:
        (mejor_match, score) o (None, 0) si no hay match
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


# =============================================================================
# Keyword Triggers - Respuestas automaticas sin LLM
# =============================================================================

KEYWORD_RESPONSES = {
    # Saludos
    r"\b(hola|buenos dias|buenas tardes|buenas noches|hey)\b": None,  # None = ir a welcome
    
    # Horarios
    r"\b(horario|hora|atencion|abierto)\b": 
        "Nuestro horario de atencion es 24/7. Un agente siempre esta disponible para ayudarle.",
    
    # Contacto
    r"\b(telefono|llamar|numero|contacto|whatsapp)\b":
        "Puede contactarnos por este WhatsApp o llamar al +1-800-XXX-XXXX.",
    
    # Urgencias
    r"\b(urgente|emergencia|sin servicio|no funciona nada)\b":
        "Entendemos que es urgente. Un tecnico revisara su caso de inmediato. Por favor indique su direccion.",
    
    # Agradecimientos
    r"\b(gracias|muchas gracias|excelente|genial)\b":
        "Con gusto! Estamos para ayudarle. Escriba *menu* si necesita algo mas.",
    
    # Despedidas
    r"\b(adios|bye|chao|hasta luego)\b":
        "Hasta pronto! Fue un placer atenderle. Escriba *hola* cuando nos necesite.",
    
    # Precios
    r"\b(precio|costo|cuanto cuesta|cuanto vale|tarifa)\b":
        "Tenemos planes desde $20/mes. Escriba *2* para ver todos nuestros planes.",
    
    # Pagos
    r"\b(pagar|pago|donde pago|como pago)\b":
        "Puede pagar por transferencia o tarjeta. Escriba *3* para opciones de pago.",
    
    # Velocidad/Internet
    r"\b(velocidad|megas|rapido|lento|internet)\b":
        "Si tiene problemas de velocidad, escriba *1* para soporte tecnico. Si quiere ver planes, escriba *2*.",
}


def check_keyword_trigger(message):
    """
    Verificar si el mensaje activa una respuesta automatica
    
    Returns:
        str: respuesta automatica, None si debe ir a welcome, False si no hay trigger
    """
    message_lower = message.lower().strip()
    
    for pattern, response in KEYWORD_RESPONSES.items():
        if re.search(pattern, message_lower, re.IGNORECASE):
            logger.info(f"Keyword trigger: {pattern}")
            return response  # None significa ir a welcome
    
    return False  # No hubo match


# =============================================================================
# Sentiment Analysis
# =============================================================================

def analyze_sentiment(text):
    """
    Analizar sentimiento del mensaje
    
    Returns:
        dict: {
            "polarity": float (-1 a 1),
            "is_negative": bool,
            "is_frustrated": bool,
            "needs_human": bool
        }
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


# =============================================================================
# Entity Extraction
# =============================================================================

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


# =============================================================================
# Extraccion de Nickname
# =============================================================================

def extract_nickname(text):
    """
    Extraer nickname/nombre del mensaje del usuario
    
    Patrones soportados:
    - "hola soy Carlos" -> Carlos
    - "buenas, Juan Perez" -> Juan
    - "me llamo Maria" -> Maria
    - "soy el ingeniero Pedro" -> Pedro
    
    Returns:
        str: nickname extraido o None
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


# =============================================================================
# Respuestas Progresivas
# =============================================================================

# Respuestas con 3 niveles de detalle
PROGRESSIVE_RESPONSES = {
    "reiniciar_router": {
        1: "Para reiniciar su router:\n1. Desconecte el cable de corriente\n2. Espere 30 segundos\n3. Vuelva a conectar\n4. Espere 2 minutos a que las luces se estabilicen\n\nEsto resuelve el 80% de los problemas de conexion.",
        2: "Desconecte el router 30 seg y reconecte. Espere 2 min.",
        3: "Reinicie el router (desconectar/reconectar)."
    },
    "verificar_pago": {
        1: "Para verificar su pago:\n1. Entre a pagos.ejemplo.com\n2. Ingrese su numero de cuenta\n3. Vera el historial de pagos\n\nSi pago recientemente, puede tardar 24-48h en reflejarse.",
        2: "Revise en pagos.ejemplo.com con su numero de cuenta.",
        3: "Consulte pagos.ejemplo.com"
    },
    "sin_servicio": {
        1: "Entiendo que no tiene servicio. Vamos a verificar:\n1. Revise que el router tenga luces encendidas\n2. Verifique que los cables esten bien conectados\n3. Intente reiniciar el router\n\nSi el problema persiste, crearemos un ticket de soporte.",
        2: "Verifique luces del router y cables. Si persiste, creamos ticket.",
        3: "Revise router. Creamos ticket si no funciona."
    },
    "cambiar_plan": {
        1: "Para cambiar de plan:\n1. Escriba *2* para ver planes disponibles\n2. Seleccione el plan deseado\n3. Un asesor se comunicara para confirmar el cambio\n\nEl cambio se aplica en su proximo ciclo de facturacion.",
        2: "Escriba *2* para ver planes. Un asesor confirmara el cambio.",
        3: "Escriba *2* y seleccione su nuevo plan."
    }
}


def get_progressive_response(topic, interaction_count):
    """
    Obtener respuesta segun nivel de interaccion
    
    Args:
        topic: tema de la respuesta (key en PROGRESSIVE_RESPONSES)
        interaction_count: numero de veces que se ha preguntado lo mismo
    
    Returns:
        str: respuesta apropiada al nivel, o None si no existe el topic
    """
    if topic not in PROGRESSIVE_RESPONSES:
        return None
    
    responses = PROGRESSIVE_RESPONSES[topic]
    
    # Nivel 1: primera vez (explicacion completa)
    # Nivel 2: segunda vez (version corta)
    # Nivel 3+: tercera vez o mas (accion directa)
    level = min(interaction_count, 3)
    
    return responses.get(level, responses.get(3))


def detect_topic_for_progressive(message):
    """
    Detectar el tema del mensaje para respuestas progresivas
    
    Returns:
        str: topic key o None
    """
    message_lower = message.lower()
    
    topic_patterns = {
        "reiniciar_router": ["reiniciar", "reinicio", "resetear", "reset", "router"],
        "verificar_pago": ["pago", "pague", "transferencia", "deposito", "abono"],
        "sin_servicio": ["sin servicio", "no funciona", "no tengo internet", "se cayo", "no hay conexion"],
        "cambiar_plan": ["cambiar plan", "otro plan", "upgrade", "mejorar plan", "subir plan"]
    }
    
    for topic, keywords in topic_patterns.items():
        if any(kw in message_lower for kw in keywords):
            return topic
    
    return None


def adjust_response_length(response, user_message_length):
    """
    Ajustar longitud de respuesta segun el estilo del usuario (lenguaje espejo)
    
    Si el usuario escribe corto, responder corto.
    Si escribe largo, dar mas detalle.
    """
    # Si el usuario escribe muy corto (< 20 chars), acortar respuesta
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
