# 🎯 Menú de Bienvenida Automático - Bot de Ventas WhatsApp

## ✨ Características Implementadas

### 1. **Menú de Bienvenida Automático**
Cuando un usuario escribe por **primera vez** al bot, recibe:
- ✅ Mensaje de bienvenida personalizado
- ✅ Botones interactivos de WhatsApp
- ✅ Opciones claras: Ver Menú, Hacer Pedido, Ayuda

### 2. **Botones Interactivos**
```
┌─────────────────────────────────┐
│ ¡Hola! Bienvenido a Mi Negocio  │
│                                  │
│ ¿Qué te gustaría hacer hoy?     │
├─────────────────────────────────┤
│  [🍔 Ver Menú]                  │
│  [🛒 Hacer Pedido]              │
│  [ℹ️ Ayuda]                     │
└─────────────────────────────────┘
```

### 3. **Detección Inteligente**
- ✅ Detecta usuarios nuevos automáticamente
- ✅ Solo muestra el menú la primera vez
- ✅ Fallback a texto si botones no funcionan

## 🚀 Cómo Funciona

### Flujo de Primer Contacto:
```
Usuario escribe "Hola" → Bot detecta que es nuevo
                          ↓
                  Envía menú con botones
                          ↓
              Usuario presiona "Ver Menú"
                          ↓
                Bot muestra catálogo completo
```

## 🎨 Personalización

### 1. Cambiar el mensaje de bienvenida
Edita `config/settings.json`:

```json
{
  "business": {
    "name": "Tu Tienda",
    "description": "¡Las mejores ofertas en electrónica!"
  }
}
```

### 2. Modificar los botones
En `src/backend/message_processor.py`, busca `send_welcome_menu`:

```python
buttons = [
    {"id": "btn_menu", "title": "🍔 Ver Menú"},
    {"id": "btn_order", "title": "🛒 Hacer Pedido"},
    {"id": "btn_help", "title": "ℹ️ Ayuda"}
]
```

**Cambia por:**
```python
buttons = [
    {"id": "btn_menu", "title": "📦 Productos"},
    {"id": "btn_order", "title": "💳 Comprar Ahora"},
    {"id": "btn_help", "title": "📞 Soporte"}
]
```

### 3. Agregar más opciones
Los botones de WhatsApp tienen limitaciones:
- **Máximo 3 botones** por mensaje
- **Máximo 20 caracteres** por botón

Para más opciones, usa **listas interactivas**:

```python
sections = [
    {
        "title": "Productos",
        "rows": [
            {"id": "cat_001", "title": "Electrónica"},
            {"id": "cat_002", "title": "Ropa"},
            {"id": "cat_003", "title": "Hogar"}
        ]
    }
]

await whatsapp_client.send_interactive_list(
    phone,
    body_text="Selecciona una categoría:",
    button_text="Ver Categorías",
    sections=sections
)
```

## 🔧 Configuración Avanzada

### Deshabilitar menú automático
Si quieres que el usuario escriba primero un comando:

En `src/backend/message_processor.py`, comenta estas líneas:

```python
# if user_created or not session.get("has_seen_welcome"):
#     await self.send_welcome_menu(phone)
#     session["has_seen_welcome"] = True
#     session_manager.save_session(phone, session)
#     return
```

### Mostrar menú cada vez
Cambia `has_seen_welcome` para que siempre sea `False`.

### Horarios de atención
El bot automáticamente detecta si está cerrado:

```json
{
  "delivery": {
    "working_hours": {
      "monday": {"open": "09:00", "close": "21:00"},
      "sunday": {"open": "10:00", "close": "20:00"}
    }
  }
}
```

Si está cerrado, mostrará:
```
🔒 Actualmente estamos cerrados
Horarios de atención:
Lunes a Viernes: 9:00 - 21:00
¡Te esperamos pronto!
```

## 📱 Tipos de Mensajes Soportados

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| **Texto** | Mensaje simple | "Hola", "Quiero un pedido" |
| **Botones** | Hasta 3 opciones | [Ver Menú] [Pedido] [Ayuda] |
| **Listas** | Hasta 10 opciones | Categorías, Productos |
| **Comandos** | Atajos directos | `menu`, `pedido`, `ayuda` |

## 🎯 Comandos Disponibles

Los usuarios pueden escribir directamente:

```
menu / menú     → Muestra el catálogo completo
pedido / orden  → Inicia proceso de compra
horario         → Horarios de atención
ayuda / help    → Información de ayuda
cancelar        → Cancela pedido actual
estado          → Consulta estado de pedido
```

## 🧪 Probar el Menú

Después de desplegar:

1. **Borra tu chat con el bot** (para simular usuario nuevo)
2. Escribe "Hola"
3. Deberías ver los botones interactivos
4. Presiona cualquier botón
5. El bot responderá según tu selección

## 🔄 Actualizar Cambios

Después de editar:

```bash
# Reiniciar el backend
docker-compose restart backend

# O rebuild si cambiaste código
docker-compose build backend
docker-compose up -d
```

## 💡 Mejores Prácticas

✅ **Mantén el mensaje corto** - Máximo 2-3 líneas  
✅ **Usa emojis** - Hacen más atractivo el menú  
✅ **Botones claros** - Nombres descriptivos (máx 20 chars)  
✅ **Fallback** - Siempre menciona comandos de texto  
✅ **Horarios** - Configura correctamente para evitar frustraciones

## 🎨 Ejemplo de Menú para Tienda de Ropa

```python
welcome = "¡Hola! Bienvenido a *Moda Express* 👗\n\n"
welcome += "Encuentra las últimas tendencias en moda\n\n"
welcome += "¿Qué buscas hoy?"

buttons = [
    {"id": "btn_women", "title": "👩 Mujer"},
    {"id": "btn_men", "title": "👨 Hombre"},
    {"id": "btn_offers", "title": "🔥 Ofertas"}
]
```

## 🍕 Ejemplo de Menú para Restaurante

```python
welcome = "¡Hola! Bienvenido a *Pizza House* 🍕\n\n"
welcome += "Las mejores pizzas de la ciudad\n\n"
welcome += "¿Qué te gustaría hacer?"

buttons = [
    {"id": "btn_menu", "title": "🍕 Ver Menú"},
    {"id": "btn_order", "title": "🛵 Ordenar Ya"},
    {"id": "btn_promos", "title": "💰 Promociones"}
]
```

## 📊 Monitoreo

Ver cuántos usuarios nuevos han recibido el menú:

```bash
docker-compose logs backend | grep "user_created"
docker-compose logs backend | grep "interactive_message_sent"
```
