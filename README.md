# Bot WhatsApp ISP - Soporte Técnico Automatizado 🤖

Bot inteligente para soporte técnico de ISP con **RAG (BM25)**, integrado con Twilio WhatsApp y potenciado por LLM (Llama 3 vía Groq).

## 🚀 Características v2.1 (Simplificada)

### 🧠 Inteligencia Eficiente
- **RAG Local**: Base de conocimiento con búsqueda rápida BM25 (sin necesidad de GPU/OpenAI).
- **LLM Groq**: Respuestas ultrarrápidas usando Llama 3 desde la nube.
- **NLP Basado en Reglas**: Clasificación de intenciones robusta y veloz.

### 🛡️ Robustez y Simplicidad
- **Arquitectura Unificada**: Todo el motor en 5 archivos clave dentro de `src/core/`.
- **Persistencia Directa**: Base de datos y memoria del bot guardadas localmente en `./data`.
- **Dockerizado**: Un solo `Dockerfile` para un despliegue instantáneo.

---

## 🛠️ Inicio Rápido

### 1. Variables de Entorno
Crea un archivo `.env` basado en la siguiente estructura:

```bash
# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=whatsapp:+1...

# IA
GROQ_API_KEY=gsk_...

# Base de Datos
POSTGRES_USER=chatbot
POSTGRES_PASSWORD=chatbot_password
POSTGRES_DB=chatbot_db
DATABASE_URL=postgresql+psycopg2://chatbot:chatbot_password@postgres:5432/chatbot_db
```

### 2. Despliegue con Docker
```bash
# Iniciar servicios
docker compose up -d

# Inicializar base de datos (Primera vez)
docker compose exec app python scripts/reset_db.py

# Aprender documentos de docs/
docker compose exec app python scripts/update_rag.py
```

---

## 📁 Estructura del Proyecto

```
bot_whatsapp/
├── app.py              # Entrada principal (FastAPI + Webhook)
├── src/core/           # El "Motor" del Bot
│   ├── config.py       # Configuración y Helpers
│   ├── database.py     # Modelos y SQL
│   ├── knowledge.py    # RAG y conexión a IA
│   ├── bot.py          # Lógica de chats y NLP
│   └── api.py          # Rutas de administración
├── docs/               # Suelta tus manuales aquí (PDF, MD, TXT)
├── data/               # Memoria persistente (Base de datos e índices)
└── scripts/            # Herramientas de mantenimiento
```

---

## 🧪 Pruebas y Mantenimiento

### Ejecutar Test de Integración
Verifica que todo el flujo (NLP -> DB -> RAG) funcione correctamente:
```bash
docker compose exec app pytest scripts/test_conversation_lifecycle.py -v
```

### Ver Logs en Tiempo Real
```bash
docker compose logs -f app
```

### Actualizar Conocimiento
Si añades archivos a `docs/`, ejecuta:
```bash
docker compose exec app python scripts/update_rag.py
```

### Inspección de Base de Datos
Accede al contenedor para ver usuarios, mensajes y tickets:
```bash
docker compose exec postgres psql -U chatbot -d chatbot_db

# Comandos útiles:
\dt                  # Listar tablas
SELECT * FROM users; # Ver clientes registrados
\q                   # Salir
```

---


## 📝 Licencia
MIT License
