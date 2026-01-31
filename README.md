# Bot WhatsApp ISP - Soporte Técnico Automatizado 

Bot inteligente para soporte técnico de ISP con **RAG vectorial**, integrado con WhatsApp Cloud API y potenciado por LLM.

##  Características v2.0

###  Inteligencia Avanzada
- **RAG Vectorial**: Base de conocimiento con búsqueda semántica (FAISS)
- **LLM Controlado**: Responde SOLO desde documentación recuperada
- **NLP Limitado**: Clasificación de intents con whitelist

###  Robustez
- **Idempotencia**: Evita mensajes duplicados (Redis)
- **Sesiones 24h**: Memoria conversacional extendida
- **Arquitectura Unificada**: 1 servicio, 1 Dockerfile

###  Base de Conocimiento
- Documentos en `docs/` (PDF, DOCX, MD, TXT)
- Actualización sin código: agregar docs y ejecutar script
- Búsqueda semántica con embeddings OpenAI

##  Inicio Rápido

### 1. Variables de Entorno

```bash
cp .env.example .env
```

Editar `.env` con:
```bash
# WhatsApp
WHATSAPP_ACCESS_TOKEN=EAA...
WHATSAPP_PHONE_ID=123...
WHATSAPP_VERIFY_TOKEN=tu_token_secreto

# IA
GROQ_API_KEY=gsk_...          # LLM


# BD
DATABASE_URL=postgresql://...
REDIS_URL=redis://redis:6379

# Dominio
DOMAIN=bot.tudominio.com
```

### 2. Deploy

```bash
# Build
docker build -t bot_whatsapp:v2 .

# Iniciar servicios
docker-compose up -d

# Inicializar base de datos
docker-compose exec app python init_db.py

# Inicializar vector store
docker-compose exec app python scripts/update_rag.py
```

### 3. Configurar Webhook en Meta

- URL: `https://tudominio.com/webhook`
- Verify Token: (el de tu .env)
- Suscribirse a: `messages`

## 📁 Estructura

```
bot_whatsapp/
├── app.py                      # App unificada (webhook + backend)
├── Dockerfile                  # Build único
├── docker-compose.yml          # 1 servicio
├── requirements.txt            # Dependencies
│
├── src/
│   ├── backend/
│   │   ├── message_processor.py   # Idempotencia + flujo
│   │   ├── session_manager.py     # Sesiones 24h
│   │   ├── nlp_service.py         # Clasificación intents
│   │   ├── support_service.py     # RAG integrado
│   │   ├── rag_service_v2.py      # Vector DB
│   │   └── ...
│   └── utils/
│
├── docs/                       # Base conocimiento RAG
│   ├── faqs/
│   ├── manuals/
│   ├── procedures/
│   └── policies/
│
└── scripts/
    └── update_rag.py          # Actualizar vector store
```

##  Flujo del Bot

```
WhatsApp Message
    ↓
Idempotency Check (Redis)
    ↓
Load Session (24h TTL)
    ↓
NLP Classify Intent
    ↓
State Machine
    ↓
IF state=SOPORTE:
  → RAG Retrieve (FAISS)
  → LLM Generate
    ↓
Send Response
    ↓
Save Session
```

##  Comandos Útiles

### Ver Logs
```bash
docker-compose logs -f app
docker-compose logs app | grep rag_retrieval
docker-compose logs app | grep duplicate_message
```

### Actualizar Base de Conocimiento
```bash
# 1. Agregar documentos
cp nuevo_manual.pdf docs/manuals/
cp faqs.md docs/faqs/

# 2. Actualizar vector store
docker-compose exec app python scripts/update_rag.py

# 3. Reiniciar (opcional)
docker-compose restart app
```

### Probar Bot en Terminal

**Opción 1: Solo Groq (más simple, sin RAG)**
```bash
# 1. Instalar dependencias ligeras
pip install -r requirements-dev.txt

# 2. Configurar solo GROQ_API_KEY en .env
echo "GROQ_API_KEY=gsk_..." >> .env

# 3. Chatear con el bot
python scripts/test_chat_simple.py
```

**Opción 2: Con Docker (completo con RAG)**
```bash
# Chat interactivo con RAG + base de datos
docker-compose exec app python scripts/test_chat.py
```

**Comandos del chat:**
- `/quit` o `/salir` - Salir
- `/clear` - Limpiar historial
- `/stats` - Ver estadísticas de uso
```

**Comandos del chat:**
- `/rag <query>` - Probar solo RAG
- `/stats` - Ver estadísticas
- `/quit` - Salir

### Health Check
```bash
curl http://localhost:8000/health
```

##  Endpoints

- `GET /` - Info del servicio
- `GET /health` - Health check
- `GET/POST /webhook` - WhatsApp webhook
- `GET /admin` - Panel admin (futuro)
- `/api/v1/*` - API backend

##  Testing

```bash
# 1. Enviar mensaje desde WhatsApp
"soporte"
"no tengo internet"

# 2. Bot responde con info de docs/faqs/

# 3. Verificar logs
docker-compose logs app | grep "rag_retrieval"
```

##  Próximos Pasos

-  Sprint 1: RAG Vectorial (completado)
-  Sprint 2: Actions Layer (reboot_ont, open_ticket, etc.)
-  Sprint 3: Escalamiento inteligente + métricas

##  Troubleshooting

### Mensajes duplicados
```bash
# Verificar idempotencia en Redis
docker exec -it chatbot_redis redis-cli
> KEYS processed:*
```

### RAG no funciona
```bash
# Verificar vector store existe
docker-compose exec app ls -la data/vector_store/

# Reinicializar
docker-compose exec app python scripts/update_rag.py
```

### Bot no responde
```bash
# Ver logs de errores
docker-compose logs app | grep ERROR

# Verificar health
curl http://localhost:8000/health
```

##  Licencia

MIT License

---

**Versión:** 1.0.0  
**Estado:**  Producción  
**Soporte:** Ver logs con `docker-compose logs app`
