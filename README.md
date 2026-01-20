# WhatsApp Chatbot Bot 🤖

Sistema de chatbot inteligente para WhatsApp Business con gestión de pedidos, NLP, y soporte multi-LLM.

## Stack

- **Backend**: FastAPI + Python 3.11+
- **Database**: PostgreSQL + Redis
- **AI**: OpenAI/Claude/Groq + RAG + NLP
- **Deploy**: Docker Compose

## Arquitectura

```
WhatsApp API → Webhook (8001) → Backend (8000) → PostgreSQL
                                      ↓           + Redis
                                NLP + RAG + LLM
```

## Despliegue en VPS

### 1. Requisitos

- Docker 20+ y Docker Compose
- Puertos 8000, 8001 abiertos
- Dominio con SSL (Nginx/Caddy recomendado)

### 2. Configuración

```bash
# Clonar
git clone <repo> && cd bot_whatsapp

# Configurar entorno
cp .env.example .env
nano .env
```

**Variables obligatorias:**

```bash
# Dominio (para Traefik)
DOMAIN=bot.tu-dominio.com

# WhatsApp (Meta Business)
WHATSAPP_VERIFY_TOKEN=token_secreto_unico
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxx
WHATSAPP_PHONE_ID=123456789
WHATSAPP_BUSINESS_ID=123456789

# Base de datos
POSTGRES_PASSWORD=CAMBIAR_PASSWORD_SEGURA
DATABASE_URL=postgresql://chatbot:CAMBIAR_PASSWORD_SEGURA@postgres:5432/chatbot_db

# Seguridad
SECRET_KEY=generar-clave-aleatoria-minimo-32-caracteres

# LLM (opcional, elegir uno)
OPENAI_API_KEY=sk-xxx          # GPT
ANTHROPIC_API_KEY=sk-ant-xxx   # Claude
GROQ_API_KEY=gsk_xxx           # Groq (gratis)
```

### 3. Crear red de Traefik

```bash
# Si no existe
docker network create traefik_net
```

### 4. Iniciar servicios

```bash
# Construir y levantar
docker-compose up -d

# Verificar estado
docker-compose ps

# Inicializar DB
docker-compose exec backend python init_db.py

# Ver logs
docker-compose logs -f
```

### 5. Configurar Webhook en Meta

1. Ir a https://developers.facebook.com/apps/
2. Configurar Webhook URL: `https://tu-dominio.com/webhook`
3. Token de verificación: usar mismo de `WHATSAPP_VERIFY_TOKEN`
4. Suscribirse a eventos: `messages`

### 6. Configuración de Negocio

Editar `/config/settings.json`:

```json
{
  "business_name": "Tu Negocio",
  "schedule": {
    "monday": {"open": "09:00", "close": "20:00"},
    ...
  },
  "delivery_zones": [
    {"name": "Zona Centro", "fee": 5.0, "time_minutes": 30}
  ],
  "products": [...]
}
```

## Gestión

### Comandos útiles

```bash
# Iniciar servicios
docker-compose up -d

# Detener servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Ver logs en vivo
docker-compose logs -f backend

# Backup base de datos
docker-compose exec postgres pg_dump -U chatbot chatbot_db > backup.sql

# Restaurar backup
cat backup.sql | docker-compose exec -T postgres psql -U chatbot chatbot_db

# Shell en backend
docker-compose exec backend bash

# Shell en PostgreSQL
docker-compose exec postgres psql -U chatbot -d chatbot_db
```

### Actualizar código

```bash
git pull
docker-compose build --no-cache
docker-compose up -d
```

## Monitoreo

### Health Check

```bash
curl http://localhost:8000/health
# Respuesta: {"status":"healthy","database":"connected","redis":"connected"}
```

### Logs

```bash
# Ver logs de backend
docker-compose logs -f backend

# Ver logs de webhook
docker-compose logs -f webhook

# Ver logs de PostgreSQL
docker-compose logs -f postgres

# Ver todas las últimas 100 líneas
docker-compose logs --tail=100
```

### Métricas

- Prometheus: `http://localhost:8000/metrics`
- Logs: `./logs/`

## Reverse Proxy (Traefik)

El proyecto está configurado para usar Traefik como reverse proxy con SSL automático.

### Requisitos previos:

1. **Red Docker de Traefik**:
```bash
docker network create traefik_net
```

2. **Variable de dominio en `.env`**:
```bash
DOMAIN=bot.tu-dominio.com
```

### Configuración automática

El `docker-compose.yml` ya incluye los labels de Traefik:

- **Backend API**: `https://tu-dominio.com/` (puerto 8000)
- **Webhook**: `https://tu-dominio.com/webhook` (puerto 8001, prioridad alta)
- **SSL**: Certificado automático con Let's Encrypt
- **Rate limiting**: Backend 100 req/s, Webhook 20 req/s

### Verificar configuración:

```bash
# Ver si Traefik detecta los servicios
docker logs traefik | grep chatbot

# Verificar redes
docker network inspect traefik_net

# Test de webhook
curl https://tu-dominio.com/webhook
```

Ver **SECURITY.md** para configuración completa de Traefik.

## Troubleshooting

### Servicios no inician

```bash
# Ver logs detallados
docker-compose logs

# Verificar puertos en uso
sudo netstat -tulpn | grep -E '8000|8001|5432|6379'

# Reconstruir desde cero
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Webhook no recibe mensajes

1. Verificar URL pública accesible
2. Verificar token en `.env` coincide con Meta
3. Verificar logs: `docker-compose logs webhook`
4. Test manual: `curl https://tu-dominio.com/webhook?hub.verify_token=TU_TOKEN&hub.challenge=test`

### Base de datos errores

```bash
# Reiniciar PostgreSQL
docker-compose restart postgres

# Verificar conectividad
docker-compose exec backend python -c "from backend.database import engine; print(engine.connect())"

# Reinicializar (⚠️ borra datos)
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose exec backend python init_db.py
```

## Seguridad

### Producción checklist

- [ ] Cambiar contraseñas por defecto en `.env`
- [ ] Usar SSL/HTTPS (Certbot + Let's Encrypt)
- [ ] Firewall: solo puertos 80, 443, 22 abiertos
- [ ] Actualizar Docker periódicamente
- [ ] Backups automáticos de PostgreSQL
- [ ] Rate limiting en Nginx
- [ ] Monitorear logs de errores
- [ ] Variables secretas nunca en código

### Backups automáticos (cron)

```bash
# Agregar a crontab
0 2 * * * cd /ruta/bot_whatsapp && docker-compose exec -T postgres pg_dump -U chatbot chatbot_db | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

## Estructura del Proyecto

```
.
├── docker-compose.yml       # Orquestación de servicios
├── .env                     # Variables de entorno
├── requirements.txt         # Dependencias Python
├── init_db.py              # Inicialización de DB
├── config/
│   ├── settings.json       # Configuración del negocio
│   └── knowledge_base.json # Base de conocimiento RAG
├── docker/
│   ├── Dockerfile.backend  # Backend container
│   └── Dockerfile.webhook  # Webhook container
├── src/
│   ├── backend/            # Lógica principal
│   │   ├── app.py         # FastAPI app
│   │   ├── message_processor.py  # Estado de conversación
│   │   ├── llm_service.py        # Integración LLM
│   │   ├── rag_service.py        # RAG + vectores
│   │   ├── nlp_service.py        # NLP + intents
│   │   ├── whatsapp_client.py    # WhatsApp API
│   │   ├── session_manager.py    # Redis sessions
│   │   ├── database.py           # PostgreSQL
│   │   └── models.py             # SQLAlchemy models
│   ├── webhook/           # Webhook receiver
│   │   └── app.py
│   └── utils/             # Helpers
└── logs/                  # Logs persistentes
```

## API Endpoints

- `GET /health` - Health check
- `POST /webhook` - WhatsApp webhook
- `GET /webhook` - Webhook verification
- `GET /metrics` - Prometheus metrics
- `GET /orders/{user_id}` - Lista de pedidos
- `POST /products` - Crear producto

## Features

### Bot Conversacional
- Flujo por estados (saludo, menú, pedido, pago, confirmación)
- Detección de intents automática
- Respuestas contextuales con historial
- Escalamiento a humano cuando es necesario

### Sistema de Pedidos
- Catálogo dinámico con categorías
- Carrito de compras
- Métodos de pago múltiples
- Cálculo de delivery por zonas
- Tracking de pedidos

### NLP & AI
- Clasificación de intenciones (15+)
- Extracción de entidades (teléfono, email, direcciones)
- Análisis de sentimiento
- RAG con base de conocimiento
- Generación de respuestas con LLM (OpenAI/Claude/Groq)

## Licencia

MIT

## Soporte

Para problemas, revisar logs: `docker-compose logs -f`
