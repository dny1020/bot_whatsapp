# WhatsApp Chatbot Platform - Production Ready 🚀

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

Sistema de chatbot inteligente para WhatsApp Business con arquitectura determinista, gestión de pedidos, NLP avanzado, y soporte para múltiples modelos LLM.

## ✨ Características Principales

### 🤖 Bot Conversacional Inteligente
- **Flujo basado en estados** con máquina de estados determinista
- **NLP avanzado**: Clasificación de intents, extracción de entidades, análisis de sentimiento
- **Integración LLM**: Soporte para OpenAI, Anthropic Claude, Groq, y modelos locales
- **RAG (Retrieval-Augmented Generation)**: Base de conocimiento con búsqueda semántica
- **Respuestas contextuales** basadas en historial de conversación

### 🛍️ Sistema de Pedidos Completo
- Catálogo de productos dinámico con categorías
- Carrito de compras con gestión de cantidades
- Múltiples métodos de pago (Efectivo, Tarjeta, Transferencia)
- Cálculo de costos de entrega por zonas
- Confirmación y tracking de pedidos

### 🚚 Gestión de Delivery
- Zonas de entrega configurables con tarifas
- Estimación de tiempos de entrega
- Validación de direcciones
- Horarios de atención por día

### 💾 Arquitectura Robusta
- **PostgreSQL**: Persistencia de usuarios, pedidos, productos, mensajes
- **Redis**: Gestión de sesiones con TTL automático
- **FastAPI**: API REST de alto rendimiento
- **Docker**: Despliegue containerizado listo para producción
- **Logs estructurados**: Trazabilidad completa con structlog

### 🧠 Inteligencia Artificial
- **Clasificación de intents**: 15+ intenciones detectadas automáticamente
- **Extracción de entidades**: Teléfonos, emails, direcciones, cantidades
- **Análisis de sentimiento**: Detección de satisfacción/insatisfacción
- **Escalamiento inteligente**: Transferencia a humano en casos complejos
- **RAG**: Búsqueda en base de conocimiento para respuestas precisas

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     WhatsApp Cloud API                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   Webhook     │  (Puerto 8001)
                 │   Receiver    │  Valida y enruta mensajes
                 └───────┬───────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │         Backend Core              │  (Puerto 8000)
         │  ┌────────────────────────────┐  │
         │  │   Message Processor        │  │  ← Cerebro
         │  │   (Estado + Router)        │  │
         │  └─────────┬──────────────────┘  │
         │            │                      │
         │  ┌─────────▼─────────────────┐  │
         │  │  NLP Service              │  │  ← Análisis
         │  │  • Intent Classification  │  │
         │  │  • Entity Extraction      │  │
         │  │  • Sentiment Analysis     │  │
         │  └─────────┬─────────────────┘  │
         │            │                      │
         │  ┌─────────▼─────────────────┐  │
         │  │  RAG Service              │  │  ← Memoria
         │  │  • Knowledge Base         │  │
         │  │  • Semantic Search        │  │
         │  │  • Context Retrieval      │  │
         │  └─────────┬─────────────────┘  │
         │            │                      │
         │  ┌─────────▼─────────────────┐  │
         │  │  LLM Service              │  │  ← Boca
         │  │  • OpenAI / Claude        │  │
         │  │  • Groq / Local Models    │  │
         │  │  • Response Generation    │  │
         │  └───────────────────────────┘  │
         └───────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐    ┌──────────┐    ┌─────────┐
    │ Redis  │    │PostgreSQL│    │WhatsApp │
    │Session │    │  Users   │    │  API    │
    │ State  │    │  Orders  │    │  Send   │
    └────────┘    │ Products │    └─────────┘
                  │ Messages │
                  └──────────┘
```

### Flujo de Decisión (La Magia está aquí)

```
Mensaje → Preprocesamiento → Router/Lógica → Decisión:
                                              │
                    ┌─────────────────────────┼─────────────────────┐
                    ▼                         ▼                     ▼
              ¿Regla simple?           ¿Consulta DB?         ¿Necesita LLM?
              (comandos)               (productos, pedidos)   (ambiguo)
                    │                         │                     │
                    ▼                         ▼                     ▼
            Respuesta directa      ┌──────────────┐         RAG + LLM
            (70% de casos)         │ PostgreSQL   │         (10% de casos)
                                   │   Query      │
                                   └──────┬───────┘
                                          │
                                          ▼
                                    Format + Send
```

### Componentes

#### 1. Webhook (WhatsApp Cloud API)
- Recibe mensajes entrantes
- Valida tokens y verifica configuración
- Envía eventos al backend

#### 2. Backend (Cerebro del Sistema)
- **Message Processor**: Máquina de estados determinista
- **Session Manager**: Redis para contexto conversacional
- **NLP Service**: Clasificación de intents y entidades
- **RAG Service**: Base de conocimiento vectorial
- **LLM Service**: Generación de respuestas naturales

#### 3. Servicios de Datos
- **PostgreSQL**: Usuarios, pedidos, productos, mensajes
- **Redis**: Sesiones activas, caché, rate limiting

#### 4. WhatsApp Client
- Envío de mensajes de texto
- Botones interactivos
- Listas de opciones
- Imágenes y multimedia

## 🚀 Inicio Rápido

### 1. Clonar repositorio

```bash
git clone <tu-repositorio>
cd project
chmod +x setup.sh manage.sh
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

**Mínimo requerido:**

```bash
# WhatsApp Business API
WHATSAPP_VERIFY_TOKEN=tu_token_unico_secreto
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxx
WHATSAPP_PHONE_ID=123456789012345
WHATSAPP_BUSINESS_ID=123456789012345

# Base de datos
DATABASE_URL=postgresql://chatbot:password@postgres:5432/chatbot_db

# Seguridad
SECRET_KEY=genera-clave-aleatoria-32-caracteres-minimo
```

**Opcional (LLM) - Elige UNO:**

```bash
# OpenAI (Más popular)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-3.5-turbo

# O Anthropic (Mejor razonamiento)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx

# O Groq (Más rápido, gratis)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
```

### 3. Configurar tu negocio

Editar `config/settings.json` con tu menú, horarios, zonas de entrega, etc.

### 4. Levantar servicios

```bash
# Usando el script
./setup.sh

# O manualmente
docker-compose up -d
docker-compose exec backend python init_db.py
```

### 5. Configurar webhook

**Desarrollo (Ngrok):**
```bash
ngrok http 8001
# Usar URL en Meta: https://xxxxx.ngrok.io/webhook
```

**Producción:**
- Configurar dominio con HTTPS
- Registrar en Meta for Developers
- URL: `https://tudominio.com/webhook`
- Token: El de `WHATSAPP_VERIFY_TOKEN`

### 6. ¡Listo! 🎉

Envía un mensaje al número de WhatsApp y el bot responderá.

---

## 📖 Documentación Completa

- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Guía detallada de despliegue
- **[API.md](API.md)**: Documentación de la API REST (si existe)
- **[copilot-instructions.md](copilot-instructions.md)**: Filosofía de arquitectura

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
docker-compose exec backend python -m pytest

# Tests específicos
docker-compose exec backend pytest tests/test_nlp.py -v
docker-compose exec backend pytest tests/test_rag.py -v
docker-compose exec backend pytest tests/test_llm.py -v

# Con coverage
docker-compose exec backend pytest --cov=src --cov-report=html
```

---

## 🎯 Filosofía de Diseño

Este proyecto sigue el principio descrito en `copilot-instructions.md`:

> **El LLM es un módulo de salida, NO el cerebro soberano.**

### Distribución de Inteligencia:
- **70% Reglas deterministas** (comandos, validaciones, flujos)
- **20% Recuperación de datos** (SQL, RAG, APIs)
- **10% LLM** (solo para redacción y casos ambiguos)

### ¿Por qué?
- ✅ **Confiable**: Las reglas no alucinan
- ✅ **Rápido**: SQL es más rápido que LLM
- ✅ **Económico**: Menos llamadas a API = menos costo
- ✅ **Mantenible**: Lógica clara y debuggeable

El bot funciona **perfectamente sin LLM configurado**. El LLM solo mejora la experiencia en casos edge.

---

## 🔧 Stack Tecnológico

### Backend
- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para PostgreSQL
- **Redis**: Sesiones y caché
- **Pydantic**: Validación de datos
- **HTTPX**: Cliente HTTP asíncrono

### NLP/AI
- **Regex-based NLP**: Clasificación de intents sin ML
- **LLM Providers**: OpenAI, Anthropic, Groq
- **RAG**: Base de conocimiento con búsqueda semántica

### Infraestructura
- **Docker**: Containerización
- **PostgreSQL 15**: Base de datos relacional
- **Redis 7**: In-memory store
- **Nginx**: Reverse proxy (producción)

### Monitoreo
- **Structlog**: Logs estructurados en JSON
- **Prometheus**: Métricas (opcional)
- **Healthchecks**: Endpoints de salud

---

## 📂 Estructura del Proyecto

```
project/
├── src/
│   ├── backend/
│   │   ├── app.py              # FastAPI principal
│   │   ├── routes.py           # Endpoints REST
│   │   ├── models.py           # Modelos SQLAlchemy
│   │   ├── database.py         # Conexión DB
│   │   ├── session_manager.py # Gestión de sesiones Redis
│   │   ├── message_processor.py# Máquina de estados del bot
│   │   ├── whatsapp_client.py # Cliente WhatsApp API
│   │   ├── nlp_service.py     # 🆕 NLP y clasificación
│   │   ├── rag_service.py     # 🆕 RAG y knowledge base
│   │   └── llm_service.py     # 🆕 Integración LLMs
│   ├── webhook/
│   │   └── webhook.py         # Receptor de WhatsApp
│   └── utils/
│       ├── config.py          # Configuración
│       ├── logger.py          # Logging
│       └── helpers.py         # Utilidades
├── config/
│   └── settings.json          # Configuración de negocio
├── tests/                     # 🆕 Suite de tests
│   ├── test_nlp.py
│   ├── test_rag.py
│   └── test_llm.py
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.webhook
├── logs/                      # Logs de aplicación
├── .env.example              # 🆕 Template actualizado
├── docker-compose.yml        # Orquestación
├── requirements.txt          # Dependencias Python
├── setup.sh                  # Script de instalación
├── manage.sh                 # Script de gestión
├── DEPLOYMENT.md            # 🆕 Guía de despliegue
└── README.md                # Este archivo
```

---

## 🌟 Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f backend

# Reiniciar un servicio
docker-compose restart backend

# Ejecutar comando en contenedor
docker-compose exec backend python -c "from src.backend.rag_service import rag_service; print(rag_service.knowledge_base)"

# Backup de base de datos
docker-compose exec postgres pg_dump -U chatbot chatbot_db > backup.sql

# Ver sesiones activas en Redis
docker-compose exec redis redis-cli KEYS "session:*"

# Ver estado de todos los servicios
docker-compose ps
```

---

## 🔐 Seguridad

- ✅ Validación de tokens en webhook
- ✅ Sanitización de inputs de usuario
- ✅ Rate limiting configurable
- ✅ Secrets en variables de entorno (nunca en código)
- ✅ HTTPS obligatorio en producción
- ✅ Aislamiento de red con Docker

---

## 🐛 Troubleshooting

### Bot no responde
```bash
# 1. Verificar servicios
docker-compose ps

# 2. Ver logs
docker-compose logs backend webhook

# 3. Verificar webhook
curl http://localhost:8001/health

# 4. Test manual
curl -X POST http://localhost:8001/webhook \
  -H "Content-Type: application/json" \
  -d '{"entry": [{"changes": [{"value": {"messages": [...]}}]}]}'
```

### Errores de LLM
```bash
# Deshabilitar temporalmente
# En .env: ENABLE_LLM_FALLBACK=false

# Verificar API key
echo $OPENAI_API_KEY
```

Más en [DEPLOYMENT.md](DEPLOYMENT.md#-troubleshooting)

---

## 📈 Roadmap

- ✅ Webhook funcional de WhatsApp
- ✅ Backend con máquina de estados
- ✅ Gestión de sesiones y contexto
- ✅ Sistema completo de pedidos
- ✅ NLP con clasificación de intents
- ✅ Integración con múltiples LLMs
- ✅ RAG con base de conocimiento
- ✅ Tests unitarios
- ⬜ Embeddings con Sentence Transformers
- ⬜ Fine-tuning de modelo local
- ⬜ Dashboard de administración
- ⬜ Métricas y analytics avanzados
- ⬜ Soporte para voz y ubicación
- ⬜ Integración con pagos online

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork del repositorio
2. Crear branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Abrir Pull Request

---

## 📄 Licencia

Este proyecto es de código abierto. Puedes adaptarlo según tus necesidades.

---

## 💡 Créditos

Desarrollado siguiendo los principios de:
- Backend conversacional determinista
- LLM como módulo de salida, no como cerebro
- Recuperación de datos > Alucinaciones del modelo
- **70% reglas + 20% RAG + 10% LLM**

Ver [copilot-instructions.md](copilot-instructions.md) para más detalles de la filosofía.
