# 📚 Cómo Usar la Base de Conocimiento (RAG)

## 🎯 El bot consulta PRIMERO la base de conocimiento antes de usar el LLM

### **1. Archivo JSON (Más fácil)**

**Ubicación:** `config/knowledge_base.json`

```bash
cd config
cp knowledge_base.json.example knowledge_base.json
nano knowledge_base.json
```

**Agrega tu información:**
```json
[
  {
    "id": "faq_customizada",
    "type": "faq",
    "content": "¿Cuándo abren? Abrimos de lunes a sábado de 9am a 9pm.",
    "metadata": {
      "category": "horarios",
      "keywords": ["abren", "horario", "abierto", "cerrado"]
    }
  },
  {
    "id": "producto_especial",
    "type": "product",
    "content": "Pizza Familiar XL: Pizza grande con 4 ingredientes a elección. Precio: $25.99",
    "metadata": {
      "category": "pizzas"
    }
  }
]
```

### **2. Cargar PDFs o Documentos**

**Instalar dependencia:**
```bash
# Agregar a requirements.txt
echo "PyPDF2==3.0.1" >> requirements.txt

# Dentro del contenedor:
docker-compose exec backend pip install PyPDF2
```

**Cargar documentos:**
```bash
# 1. Crear carpeta para documentos
mkdir docs

# 2. Agregar tus PDFs/TXT
# - docs/manual.pdf
# - docs/politicas.txt
# - docs/faq.md

# 3. Cargar en la base de conocimiento
docker-compose exec backend python scripts/load_documents.py docs/

# O un archivo específico:
docker-compose exec backend python scripts/load_documents.py docs/manual.pdf
```

### **3. Cómo funciona el flujo RAG**

```
Usuario: "¿Hacen envíos a domicilio?"
    ↓
1. RAG busca en knowledge_base.json → ✅ Encuentra "información de envíos"
    ↓
2. Devuelve respuesta DIRECTA (sin llamar al LLM)
    ↓
Bot: "Sí, hacemos envíos gratis en pedidos mayores a $50..."
```

**Si NO encuentra respuesta en RAG:**
```
Usuario: "Pregunta muy específica o ambigua"
    ↓
1. RAG busca → ❌ No encuentra match exacto
    ↓
2. Pasa el contexto relevante al LLM
    ↓
3. LLM genera respuesta usando el contexto
```

### **4. Tipos de contenido soportados**

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `faq` | Preguntas frecuentes | "¿Cómo rastreo mi pedido?" |
| `policy` | Políticas del negocio | "Política de devoluciones" |
| `product` | Información de productos | "Pizza Margarita - $15.99" |
| `tutorial` | Guías paso a paso | "Cómo crear una cuenta" |
| `document` | Contenido de PDFs/docs | Extraído de manuales |

### **5. Estructura de carpetas recomendada**

```
project/
├── config/
│   ├── knowledge_base.json       ← Tu base de conocimiento principal
│   └── settings.json             ← Menú, horarios, zonas
├── docs/                          ← PDFs y documentos (crear)
│   ├── manual_usuario.pdf
│   ├── politicas.txt
│   └── faq.md
└── scripts/
    └── load_documents.py         ← Script para cargar PDFs
```

### **6. Comandos útiles**

```bash
# Ver cuántas entradas tienes
docker-compose exec backend python -c "from src.backend.rag_service import rag_service; print(f'Entradas: {len(rag_service.knowledge_base)}')"

# Buscar algo en la base de conocimiento
docker-compose exec backend python -c "from src.backend.rag_service import rag_service; results = rag_service.search('envío'); print(results)"

# Recargar la base de conocimiento después de editar
docker-compose restart backend
```

### **7. Configuración de RAG en .env**

```bash
# Habilitar RAG (por defecto: true)
ENABLE_RAG=true

# Usar LLM solo si RAG no encuentra respuesta (recomendado)
ENABLE_LLM_FALLBACK=true

# Si quieres usar embeddings semánticos (opcional)
USE_LOCAL_EMBEDDINGS=true
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### **8. Ejemplo completo**

**config/knowledge_base.json:**
```json
[
  {
    "id": "envios_001",
    "type": "faq",
    "content": "Hacemos envíos gratis en pedidos superiores a $50. Para montos menores, el costo de envío es de $5.",
    "metadata": {
      "keywords": ["envío", "delivery", "gratis", "costo", "domicilio"]
    }
  },
  {
    "id": "horarios_001",
    "type": "faq",
    "content": "Horarios de atención: Lunes a Viernes 10am-10pm, Sábados 12pm-11pm, Domingos cerrado.",
    "metadata": {
      "keywords": ["horario", "abierto", "cerrado", "cuándo"]
    }
  },
  {
    "id": "devoluciones_001",
    "type": "policy",
    "content": "Política de devoluciones: Aceptamos devoluciones dentro de 7 días si el producto está en mal estado. Contacta inmediatamente.",
    "metadata": {
      "keywords": ["devolución", "reembolso", "garantía", "mal estado"]
    }
  }
]
```

## 💡 Ventajas de usar RAG antes del LLM

✅ **Más rápido**: No hace llamadas a API externas  
✅ **Más barato**: No consume tokens del LLM  
✅ **Más preciso**: Respuestas exactas de tu negocio  
✅ **Más confiable**: No hay alucinaciones  
✅ **Funciona offline**: Si no tienes API key de LLM
