# 📜 Scripts de Utilidades

## Scripts Disponibles

### 1. 🔄 `update_rag.py` - Actualizar Vector Store

Actualiza el vector store con los documentos de `docs/`

**Uso:**
```bash
# Docker
docker-compose exec app python scripts/update_rag.py

# Local (requiere OPENAI_API_KEY)
python scripts/update_rag.py
```

**Cuándo usar:**
- Después de agregar nuevos documentos a `docs/`
- Después de modificar documentos existentes
- Primera vez que inicializas el sistema RAG

---

### 2. 💬 `test_chat_simple.py` - Chat Local (Recomendado)

Chat interactivo **SIN** dependencias de base de datos. Perfecto para desarrollo local.

**Uso:**
```bash
# 1. Instalar deps ligeras
pip install -r requirements-dev.txt

# 2. Ejecutar
python scripts/test_chat_simple.py
```

**Requiere solo:**
- ✅ `GROQ_API_KEY` en .env
- ❌ NO requiere OpenAI (funciona sin RAG)
- ❌ NO requiere PostgreSQL
- ❌ NO requiere Redis

**Características:**
- 🤖 Chat interactivo directo con Groq
- 📊 Métricas (tiempo, tokens)
- 🎨 Interfaz coloreada
- 💨 Super rápido para testing

---

### 3. 💬 `test_chat.py` - Chat Completo (Docker)

Chat con todas las funcionalidades. Requiere base de datos.

**Uso:**
```bash
# Solo con Docker
docker-compose exec app python scripts/test_chat.py
```

**Requiere:**
- ✅ PostgreSQL (Docker)
- ✅ Redis (Docker)
- ✅ Todas las deps

---

## 🆚 Comparación

| Característica | test_chat_simple.py | test_chat.py |
|----------------|---------------------|--------------|
| PostgreSQL | ❌ No | ✅ Sí |
| Redis | ❌ No | ✅ Sí |
| RAG | ❌ No (solo Groq) | ✅ Sí |
| LLM | ✅ Groq | ✅ Groq |
| Uso | **Local** | Docker |
| Velocidad | ⚡ Rápido | Normal |

---

## 🚀 Inicio Rápido

**Para desarrollo local (solo Groq):**
```bash
# 1. Instalar
pip install -r requirements-dev.txt

# 2. Configurar .env
GROQ_API_KEY=gsk_...

# 3. Chatear
python scripts/test_chat_simple.py
```

**Para testing completo (con RAG):**
```bash
docker-compose up -d
docker-compose exec app python scripts/test_chat.py
```

---

## 🔍 Comandos del Chat

**test_chat_simple.py:**
- `/stats` - Ver estadísticas
- `/clear` - Limpiar historial
- `/quit` - Salir

**test_chat.py:**
- `/rag <query>` - Probar solo RAG
- `/stats` - Ver estadísticas
- `/clear` - Limpiar historial
- `/quit` - Salir

---

## 📝 Ejemplo

```bash
$ python scripts/test_chat_simple.py

======================================================================
🤖 Bot WhatsApp - Test Chat (Groq Only)
======================================================================
💡 Chat directo con Groq LLM (sin base de datos)

Comandos:
  • /quit, /salir      - Salir
  • /clear             - Limpiar historial
  • /stats             - Ver estadísticas
======================================================================

✅ Conectado a Groq: llama-3.3-70b-versatile

> Hola, tengo problemas con mi internet

👤 Tú: Hola, tengo problemas con mi internet

🤖 Bot: Lo siento mucho. ¿Podrías proporcionarme más detalles sobre 
el problema? ¿No puedes conectarte o la conexión es lenta?

⏱️  1.37s | ~89 tokens

> /stats

📊 Estadísticas:
  • Mensajes: 1
  • Tokens: ~89
  • Tiempo: 1.37s
  • Promedio: 1.37s/msg

> /quit

👋 ¡Hasta luego!
```
