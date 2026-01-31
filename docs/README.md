# Documentación RAG - ISP Support Bot

## Estructura de Documentos

Este directorio contiene la base de conocimiento que el bot usa para responder preguntas técnicas mediante RAG (Retrieval Augmented Generation).

###  Directorios

- **manuals/** - Manuales de equipos (ONT, routers, etc.)
- **faqs/** - Preguntas frecuentes
- **procedures/** - Procedimientos técnicos NOC
- **policies/** - Políticas de facturación, SLA, etc.

###  Formato de Documentos

Soportados:
- PDF (.pdf)
- Word (.docx)
- Texto (.txt)
- Markdown (.md)

###  Actualización

1. Agregar/actualizar documentos en carpetas correspondientes
2. Ejecutar: `python scripts/update_rag.py`
3. Vector DB se actualiza automáticamente

###  Estadísticas

- Chunks: Se generan automáticamente (500-800 tokens)
- Embeddings: OpenAI text-embedding-3-small
- Vector DB: FAISS (local)

###  Reglas

-  Documentos claros y concisos
-  Un tema por archivo
-  Actualizar regularmente
-  No incluir información sensible (contraseñas, IPs privadas)
-  No duplicar contenido entre archivos
