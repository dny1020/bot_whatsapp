# ISP Support WhatsApp Bot 🌐🤖

Chatbot inteligente para soporte técnico de ISP (Proveedor de Internet), integrado con la API oficial de WhatsApp (Meta) y potenciado por LLM (Groq/Llama-3) con base de conocimientos local.

## 🚀 Inicio Rápido

### 1. Requisitos
- Docker y Docker Compose
- Cuenta en Meta Developers y Groq Cloud (API Key)

### 2. Configuración
```bash
cp .env.example .env
# Edita .env con tus credenciales de Meta y Groq
```

**Variables Clave:**
- `WHATSAPP_ACCESS_TOKEN`: Token permanente de Meta.
- `WHATSAPP_PHONE_ID`: ID del número de WhatsApp.
- `GROQ_API_KEY`: Para la inteligencia del soporte técnico.
- `DOMAIN`: Tu dominio para el webhook (ej: bot.tudominio.com).

### 3. Despliegue
```bash
# 1. Autenticar con GHCR (necesario para descargar las imágenes)
echo $GH_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USER --password-stdin

# 2. Iniciar contenedores
docker-compose up -d

# 3. Inicializar base de datos
docker-compose exec backend python init_db.py
```

## 🛠️ Comandos de Gestión
- **Logs en vivo**: `docker-compose logs -f backend`
- **Reiniciar**: `docker-compose restart`
- **Actualizar**: `git pull && docker-compose build && docker-compose up -d`

## 🧠 Características
- **Soporte IA**: Respuestas inteligentes basadas en una base de conocimientos local (`config/knowledge_base.json`).
- **Comandos Directos**: `soporte`, `planes`, `factura`, `humano`.
- **Memoria Contextual**: Mantiene el hilo de la conversación técnica.
- **Producción Ready**: Configurado con Traefik para SSL automático y seguridad.

## 📂 Estructura
- `src/backend/`: Núcleo del bot (procesador, IA, base de datos).
- `src/webhook/`: Receptor de señales de Meta.
- `config/`: Configuración del negocio y base de conocimientos.


## 🌐 Webhook Meta
Configura en el panel de Meta:
`https://tu-dominio.com/webhook`
Suscribirse al evento: `messages`

---
MIT License | Soporte: Revisa los logs con `docker-compose logs`.
