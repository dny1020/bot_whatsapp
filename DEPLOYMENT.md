# 🚀 Guía de Despliegue - WhatsApp Chatbot

## 📋 Pre-requisitos

### Cuenta de WhatsApp Business
1. Crear cuenta en [Meta for Developers](https://developers.facebook.com/)
2. Crear una App de WhatsApp Business
3. Configurar número de teléfono
4. Obtener las credenciales:
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_PHONE_ID`
   - `WHATSAPP_BUSINESS_ID`

### Proveedor LLM (Opcional pero recomendado)

Elige UNO de estos proveedores:

#### OpenAI (Recomendado para producción)
- Crear cuenta en [OpenAI Platform](https://platform.openai.com/)
- Generar API Key
- Modelos disponibles: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo`

#### Anthropic (Claude - Mejor razonamiento)
- Crear cuenta en [Anthropic Console](https://console.anthropic.com/)
- Generar API Key
- Modelos disponibles: `claude-3-haiku-20240307`, `claude-3-sonnet-20240229`

#### Groq (Más rápido y económico)
- Crear cuenta en [Groq Console](https://console.groq.com/)
- Generar API Key
- Modelos disponibles: `llama-3.1-8b-instant`, `mixtral-8x7b-32768`

### Infraestructura
- Servidor Linux (Ubuntu 20.04+, Debian 11+)
- Docker y Docker Compose instalados
- Dominio con HTTPS (o Ngrok para desarrollo)
- Mínimo 2GB RAM, 20GB disco

---

## 🔧 Instalación

### 1. Clonar y configurar

```bash
# Clonar repositorio
git clone <tu-repo>
cd project

# Dar permisos a scripts
chmod +x setup.sh manage.sh
```

### 2. Configurar variables de entorno

```bash
# Copiar template
cp .env.example .env

# Editar con tus credenciales
nano .env
```

**Variables OBLIGATORIAS:**

```bash
# WhatsApp (CRÍTICO)
WHATSAPP_VERIFY_TOKEN=tu_token_secreto_aqui
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxx
WHATSAPP_PHONE_ID=123456789012345
WHATSAPP_BUSINESS_ID=123456789012345

# Base de datos
DATABASE_URL=postgresql://chatbot:TU_PASSWORD_SEGURO@postgres:5432/chatbot_db

# Seguridad
SECRET_KEY=genera-una-clave-aleatoria-de-32-caracteres-o-mas
```

**Variables OPCIONALES (LLM):**

Configura solo UNA de estas opciones:

```bash
# Opción 1: OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-3.5-turbo

# Opción 2: Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-haiku-20240307

# Opción 3: Groq (Gratis, rápido)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.1-8b-instant
```

### 3. Configurar negocio

Editar `config/settings.json`:

```json
{
  "business": {
    "name": "Tu Negocio",
    "description": "Descripción de tu servicio",
    "phone": "+51987654321",
    "email": "contacto@tunegocio.com"
  },
  "menu": {
    "categories": [
      {
        "id": "cat_001",
        "name": "Comidas",
        "items": [
          {
            "id": "item_001",
            "name": "Producto 1",
            "description": "Descripción del producto",
            "price": 15.99,
            "available": true
          }
        ]
      }
    ]
  },
  "delivery": {
    "zones": [...],
    "working_hours": {...}
  }
}
```

### 4. Ejecutar setup

```bash
# Ejecutar script de instalación
./setup.sh

# O manualmente:
docker-compose up -d
docker-compose exec backend python init_db.py
```

### 5. Verificar servicios

```bash
# Ver logs
docker-compose logs -f

# Verificar salud de servicios
curl http://localhost:8000/health
curl http://localhost:8001/health
```

---

## 🌐 Configurar Webhook de WhatsApp

### Desarrollo (Ngrok)

```bash
# Instalar ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# Autenticar
ngrok config add-authtoken TU_TOKEN_NGROK

# Exponer webhook
ngrok http 8001
```

### Producción (Dominio propio)

1. **Configurar Nginx:**

```nginx
server {
    listen 443 ssl;
    server_name webhook.tudominio.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. **Registrar en Meta:**

- Ir a tu App en Meta for Developers
- WhatsApp > Configuration
- Webhook URL: `https://webhook.tudominio.com/webhook`
- Verify Token: El mismo que pusiste en `WHATSAPP_VERIFY_TOKEN`
- Subscribe to: `messages`

---

## 🎛️ Gestión del Sistema

### Comandos útiles

```bash
# Iniciar servicios
docker-compose up -d

# Detener servicios
docker-compose down

# Ver logs
docker-compose logs -f backend
docker-compose logs -f webhook

# Reiniciar un servicio
docker-compose restart backend

# Ejecutar comandos en contenedor
docker-compose exec backend python -m pytest

# Ver base de datos
docker-compose exec postgres psql -U chatbot -d chatbot_db

# Ver Redis
docker-compose exec redis redis-cli
```

### Script de gestión

```bash
# Ver estado
./manage.sh status

# Reiniciar
./manage.sh restart

# Backups
./manage.sh backup

# Ver logs
./manage.sh logs backend
```

---

## 🧪 Testing

```bash
# Instalar dependencias de test
pip install -r tests/requirements-test.txt

# Ejecutar todos los tests
docker-compose exec backend python -m pytest

# Tests específicos
docker-compose exec backend python -m pytest tests/test_nlp.py -v
docker-compose exec backend python -m pytest tests/test_rag.py -v
docker-compose exec backend python -m pytest tests/test_llm.py -v

# Con coverage
docker-compose exec backend python -m pytest --cov=src --cov-report=html
```

---

## 📊 Monitoreo

### Logs estructurados

Los logs se guardan en `logs/`:
- `logs/app.log` - Aplicación general
- `logs/webhook.log` - Webhook de WhatsApp
- `logs/error.log` - Errores

### Healthchecks

```bash
# Backend
curl http://localhost:8000/health

# Webhook
curl http://localhost:8001/health

# PostgreSQL
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping
```

### Métricas (Prometheus - Opcional)

Si `PROMETHEUS_ENABLED=true`:
- Métricas disponibles en `http://localhost:8000/metrics`

---

## 🔒 Seguridad

### Recomendaciones

1. **Variables de entorno:**
   - Nunca commitear el archivo `.env`
   - Usar passwords fuertes y únicos
   - Rotar tokens regularmente

2. **Red:**
   - Usar HTTPS en producción
   - Configurar firewall (solo puertos 80, 443)
   - Limitar acceso a base de datos

3. **WhatsApp:**
   - Validar siempre `WHATSAPP_VERIFY_TOKEN`
   - Verificar firma de mensajes (opcional)

4. **Rate limiting:**
   - Configurar `RATE_LIMIT_PER_MINUTE` según tu plan

---

## 🐛 Troubleshooting

### El webhook no recibe mensajes

```bash
# 1. Verificar que el servicio esté corriendo
curl http://localhost:8001/health

# 2. Verificar logs
docker-compose logs webhook

# 3. Probar el endpoint manualmente
curl -X GET "http://localhost:8001/webhook?hub.mode=subscribe&hub.verify_token=TU_TOKEN&hub.challenge=test"

# 4. Verificar configuración en Meta
# - URL correcta
# - Token correcto
# - Subscriptions activas
```

### El bot no responde

```bash
# 1. Verificar Redis
docker-compose exec redis redis-cli ping

# 2. Verificar PostgreSQL
docker-compose exec postgres pg_isready

# 3. Ver logs del backend
docker-compose logs backend | grep ERROR

# 4. Verificar token de WhatsApp
# - No expirado
# - Permisos correctos
```

### Errores de LLM

```bash
# Verificar API key
echo $OPENAI_API_KEY  # o la que uses

# Probar conexión
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Deshabilitar LLM temporalmente
# En .env:
ENABLE_LLM_FALLBACK=false
```

---

## 📈 Escalado

### Horizontal (Múltiples instancias)

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    
  webhook:
    deploy:
      replicas: 2
```

### Vertical (Más recursos)

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Base de datos

- Considerar PostgreSQL managed (RDS, DigitalOcean)
- Redis Cluster para alta disponibilidad
- Backups automáticos diarios

---

## 🔄 Actualizaciones

```bash
# 1. Backup
./manage.sh backup

# 2. Pull cambios
git pull origin main

# 3. Rebuild
docker-compose build

# 4. Migrar DB si es necesario
docker-compose exec backend alembic upgrade head

# 5. Restart
docker-compose up -d
```

---

## 📞 Soporte

- Issues: GitHub Issues
- Documentación: `/docs` en el servidor
- Logs: `logs/` directory

---

## ✅ Checklist de Producción

- [ ] Variables de entorno configuradas
- [ ] WhatsApp webhook registrado y verificado
- [ ] LLM API configurada y funcionando
- [ ] HTTPS configurado
- [ ] Backups automáticos configurados
- [ ] Monitoreo activo
- [ ] Firewall configurado
- [ ] Logs rotando correctamente
- [ ] Tests pasando
- [ ] Menú y configuración de negocio actualizada
