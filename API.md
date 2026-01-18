# 🔌 Guía de APIs - WhatsApp Chatbot

## 📡 Endpoints Disponibles

### Backend API (Puerto 8000)

Base URL: `http://localhost:8000` (desarrollo) o `https://api.tudominio.com` (producción)

---

## 🏥 Health & Status

### GET `/health`

Verifica el estado del servicio.

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-09T22:00:00.000Z",
  "environment": "production"
}
```

**Ejemplo:**
```bash
curl http://localhost:8000/health
```

---

### GET `/`

Información básica del servicio.

**Respuesta:**
```json
{
  "service": "whatsapp-chatbot-backend",
  "version": "1.0.0",
  "status": "running"
}
```

---

## 👥 Usuarios

### GET `/api/v1/users`

Listar todos los usuarios.

**Query Parameters:**
- `skip` (int): Offset para paginación (default: 0)
- `limit` (int): Límite de resultados (default: 100)

**Respuesta:**
```json
[
  {
    "id": 1,
    "phone": "51987654321",
    "name": "Juan Pérez",
    "email": "juan@example.com",
    "created_at": "2026-01-01T10:00:00Z",
    "updated_at": "2026-01-09T15:30:00Z"
  }
]
```

**Ejemplo:**
```bash
curl http://localhost:8000/api/v1/users?limit=10
```

---

### GET `/api/v1/users/{user_id}`

Obtener un usuario específico.

**Respuesta:**
```json
{
  "id": 1,
  "phone": "51987654321",
  "name": "Juan Pérez",
  "email": "juan@example.com",
  "created_at": "2026-01-01T10:00:00Z"
}
```

---

## 📦 Pedidos

### GET `/api/v1/orders`

Listar todos los pedidos.

**Query Parameters:**
- `skip` (int): Offset
- `limit` (int): Límite
- `status` (str): Filtrar por estado (pending, confirmed, delivering, delivered)
- `user_id` (int): Filtrar por usuario

**Respuesta:**
```json
[
  {
    "id": 1,
    "order_id": "ORD-20260109-A1B2C3",
    "user_id": 1,
    "items": [
      {
        "id": "item_001",
        "name": "Pizza Margarita",
        "price": 12.99,
        "quantity": 2
      }
    ],
    "subtotal": 25.98,
    "delivery_fee": 3.00,
    "total": 28.98,
    "status": "confirmed",
    "delivery_address": "Av. Principal 123, Lima",
    "payment_method": "cash",
    "created_at": "2026-01-09T18:30:00Z",
    "confirmed_at": "2026-01-09T18:32:00Z"
  }
]
```

**Ejemplo:**
```bash
# Todos los pedidos
curl http://localhost:8000/api/v1/orders

# Pedidos de un usuario
curl http://localhost:8000/api/v1/orders?user_id=1

# Pedidos confirmados
curl http://localhost:8000/api/v1/orders?status=confirmed
```

---

### GET `/api/v1/orders/{order_id}`

Obtener detalles de un pedido.

**Respuesta:**
```json
{
  "id": 1,
  "order_id": "ORD-20260109-A1B2C3",
  "user": {
    "id": 1,
    "phone": "51987654321",
    "name": "Juan Pérez"
  },
  "items": [...],
  "total": 28.98,
  "status": "delivering",
  "delivery_address": "Av. Principal 123"
}
```

---

### PUT `/api/v1/orders/{order_id}/status`

Actualizar el estado de un pedido.

**Body:**
```json
{
  "status": "delivering"
}
```

**Valores permitidos:**
- `pending`: Pendiente de confirmación
- `confirmed`: Confirmado, en preparación
- `preparing`: En preparación
- `delivering`: En camino
- `delivered`: Entregado
- `cancelled`: Cancelado

**Respuesta:**
```json
{
  "order_id": "ORD-20260109-A1B2C3",
  "status": "delivering",
  "updated_at": "2026-01-09T19:00:00Z"
}
```

**Ejemplo:**
```bash
curl -X PUT http://localhost:8000/api/v1/orders/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "delivering"}'
```

---

## 🍕 Productos

### GET `/api/v1/products`

Listar productos del menú.

**Query Parameters:**
- `category` (str): Filtrar por categoría
- `available` (bool): Solo productos disponibles

**Respuesta:**
```json
[
  {
    "id": 1,
    "product_id": "item_001",
    "name": "Pizza Margarita",
    "description": "Salsa de tomate, mozzarella, albahaca",
    "price": 12.99,
    "category": "Comidas",
    "available": true,
    "image_url": null
  }
]
```

**Ejemplo:**
```bash
# Todos los productos
curl http://localhost:8000/api/v1/products

# Por categoría
curl http://localhost:8000/api/v1/products?category=Comidas

# Solo disponibles
curl http://localhost:8000/api/v1/products?available=true
```

---

### PUT `/api/v1/products/{product_id}/availability`

Cambiar disponibilidad de un producto.

**Body:**
```json
{
  "available": false
}
```

**Respuesta:**
```json
{
  "product_id": "item_001",
  "available": false,
  "updated_at": "2026-01-09T20:00:00Z"
}
```

---

## 💬 Mensajes

### GET `/api/v1/messages/{phone}`

Obtener historial de mensajes de un usuario.

**Query Parameters:**
- `limit` (int): Cantidad de mensajes (default: 50)

**Respuesta:**
```json
[
  {
    "id": 1,
    "direction": "inbound",
    "message_type": "text",
    "content": "Hola, quiero hacer un pedido",
    "created_at": "2026-01-09T18:00:00Z"
  },
  {
    "id": 2,
    "direction": "outbound",
    "message_type": "text",
    "content": "¡Hola! Perfecto, ¿qué deseas ordenar?",
    "created_at": "2026-01-09T18:00:01Z"
  }
]
```

**Ejemplo:**
```bash
curl http://localhost:8000/api/v1/messages/51987654321?limit=100
```

---

## 📊 Estadísticas

### GET `/api/v1/stats/orders`

Estadísticas de pedidos.

**Query Parameters:**
- `from_date` (str): Fecha inicio (ISO 8601)
- `to_date` (str): Fecha fin (ISO 8601)

**Respuesta:**
```json
{
  "total_orders": 150,
  "by_status": {
    "pending": 5,
    "confirmed": 10,
    "preparing": 8,
    "delivering": 3,
    "delivered": 120,
    "cancelled": 4
  },
  "total_revenue": 4250.50,
  "average_order_value": 28.34,
  "period": {
    "from": "2026-01-01T00:00:00Z",
    "to": "2026-01-09T23:59:59Z"
  }
}
```

**Ejemplo:**
```bash
curl "http://localhost:8000/api/v1/stats/orders?from_date=2026-01-01&to_date=2026-01-09"
```

---

### GET `/api/v1/stats/users`

Estadísticas de usuarios.

**Respuesta:**
```json
{
  "total_users": 250,
  "new_users_today": 8,
  "active_users_today": 45,
  "users_with_orders": 180
}
```

---

## 🔧 Administración

### POST `/api/v1/admin/broadcast`

Enviar mensaje broadcast a usuarios.

**Body:**
```json
{
  "message": "¡Promoción especial! 20% de descuento hoy",
  "target": "all",
  "filter": {
    "has_orders": true
  }
}
```

**Valores de `target`:**
- `all`: Todos los usuarios
- `active`: Usuarios activos (últimos 7 días)
- `filtered`: Usar filtros personalizados

**Respuesta:**
```json
{
  "broadcast_id": "BCT-20260109-XYZ",
  "sent_to": 180,
  "failed": 2,
  "status": "completed"
}
```

**Ejemplo:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/broadcast \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SECRET_KEY" \
  -d '{
    "message": "¡Promoción especial!",
    "target": "active"
  }'
```

---

## 🌐 Webhook (Puerto 8001)

### GET `/webhook`

Verificación del webhook de WhatsApp.

**Query Parameters:**
- `hub.mode`: "subscribe"
- `hub.verify_token`: Tu token de verificación
- `hub.challenge`: Challenge de Meta

**Respuesta:**
Devuelve el `challenge` si el token es correcto.

---

### POST `/webhook`

Recibe eventos de WhatsApp.

**Body (ejemplo de Meta):**
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "PHONE_NUMBER_ID"
            },
            "messages": [
              {
                "from": "51987654321",
                "id": "wamid.xxxxx",
                "timestamp": "1704835200",
                "type": "text",
                "text": {
                  "body": "Hola"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Respuesta:**
```json
{
  "status": "ok"
}
```

---

## 🔐 Autenticación

Actualmente el proyecto no implementa autenticación en los endpoints.

Para producción, se recomienda:

1. **API Keys** en headers:
```bash
curl -H "X-API-Key: your-secret-key" http://localhost:8000/api/v1/orders
```

2. **JWT Tokens**:
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." http://localhost:8000/api/v1/orders
```

3. **Basic Auth**:
```bash
curl -u admin:password http://localhost:8000/api/v1/orders
```

Implementar según necesidades en `src/backend/routes.py`.

---

## 📝 Ejemplos de Integración

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Obtener pedidos
response = requests.get(f"{BASE_URL}/api/v1/orders")
orders = response.json()

# Actualizar estado
response = requests.put(
    f"{BASE_URL}/api/v1/orders/1/status",
    json={"status": "delivering"}
)

# Obtener historial de mensajes
response = requests.get(f"{BASE_URL}/api/v1/messages/51987654321")
messages = response.json()
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

// Obtener pedidos
const orders = await axios.get(`${BASE_URL}/api/v1/orders`);
console.log(orders.data);

// Actualizar estado
await axios.put(`${BASE_URL}/api/v1/orders/1/status`, {
  status: 'delivering'
});

// Estadísticas
const stats = await axios.get(`${BASE_URL}/api/v1/stats/orders`);
console.log(stats.data);
```

### cURL

```bash
# Variables
BASE_URL="http://localhost:8000"
ORDER_ID="1"

# Listar pedidos activos
curl "$BASE_URL/api/v1/orders?status=confirmed"

# Actualizar pedido
curl -X PUT "$BASE_URL/api/v1/orders/$ORDER_ID/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "delivering"}'

# Ver estadísticas
curl "$BASE_URL/api/v1/stats/orders"
```

---

## 🔍 Códigos de Estado HTTP

| Código | Significado | Cuándo ocurre |
|--------|-------------|---------------|
| 200 | OK | Solicitud exitosa |
| 201 | Created | Recurso creado |
| 400 | Bad Request | Datos inválidos |
| 404 | Not Found | Recurso no existe |
| 422 | Unprocessable Entity | Error de validación |
| 500 | Internal Server Error | Error del servidor |

---

## 📚 Documentación Interactiva

Una vez levantado el backend, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Documentación automática generada por FastAPI.

---

## 💡 Tips

1. **Paginación**: Usa `skip` y `limit` para listas grandes
2. **Filtros**: Combina múltiples parámetros para búsquedas específicas
3. **Caching**: Redis cachea las sesiones automáticamente
4. **Rate limiting**: Configurable en `.env` con `RATE_LIMIT_PER_MINUTE`

---

## 🐛 Debugging

```bash
# Ver todos los endpoints disponibles
docker-compose exec backend python -c "from src.backend.app import app; print(app.routes)"

# Probar endpoint específico
curl -v http://localhost:8000/api/v1/orders

# Ver logs de requests
docker-compose logs -f backend | grep "REQUEST"
```
