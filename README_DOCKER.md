# RAG-Anything API Server - Docker Deployment Guide

Guía completa para desplegar RAG-Anything como API REST en **Easypanel** y conectarlo con **n8n**.

## Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Requisitos Previos](#requisitos-previos)
- [Despliegue Rápido](#despliegue-rápido)
- [Despliegue en Easypanel](#despliegue-en-easypanel)
- [API Endpoints](#api-endpoints)
- [Integración con n8n](#integración-con-n8n)
- [Variables de Entorno](#variables-de-entorno)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Troubleshooting](#troubleshooting)

---

## Descripción General

Este servidor API REST permite:

- ✅ **Subir y procesar documentos** (PDF, Office, imágenes, texto)
- ✅ **Hacer consultas inteligentes** usando RAG multimodal
- ✅ **Filtrar por documento específico** o buscar en todos
- ✅ **Listar documentos procesados**
- ✅ **Eliminar documentos** del sistema

**Stack Técnico:**
- FastAPI (servidor API REST)
- RAG-Anything + LightRAG (motor RAG)
- MinerU (parser de documentos)
- OpenAI API (LLM, vision, embeddings)

---

## Requisitos Previos

### 1. API Key de OpenAI

Necesitas una API key de OpenAI válida:
- Obtén tu key en: https://platform.openai.com/api-keys
- Asegúrate de tener créditos disponibles

### 2. Plataforma de Hosting

Opciones recomendadas:
- **Easypanel** (recomendado para este guide)
- Docker Compose (local o VPS)
- Cualquier plataforma que soporte Docker

### 3. n8n (opcional)

Para automatización y workflows:
- Instancia de n8n corriendo
- Acceso para crear HTTP Request nodes

---

## Despliegue Rápido

### Usando Docker Compose (Local)

1. **Clona el repositorio:**
```bash
git clone https://github.com/HKUDS/RAG-Anything.git
cd RAG-Anything
```

2. **Configura las variables de entorno:**
```bash
# Copia el archivo de ejemplo
cp env.example .env

# Edita .env y configura:
nano .env
```

Variables mínimas requeridas:
```env
API_KEY=tu-clave-secreta-aqui
OPENAI_API_KEY=sk-tu-openai-key-aqui
```

3. **Inicia el servidor:**
```bash
docker-compose up -d
```

4. **Verifica que está corriendo:**
```bash
curl http://localhost:8000/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "message": "RAG-Anything API is running",
  "rag_initialized": true
}
```

---

## Despliegue en Easypanel

### Opción 1: Desde GitHub (Recomendado)

1. **Sube tu código a GitHub:**
```bash
# Desde tu repositorio local
git add .
git commit -m "Add Docker API server"
git push origin main
```

2. **En Easypanel:**

   a. Ve a **Projects** → **Create Project**

   b. Selecciona **Docker** → **From Git Repository**

   c. Conecta tu repositorio de GitHub

   d. Configura el proyecto:
   - **Name**: `raganything-api`
   - **Branch**: `main`
   - **Dockerfile Path**: `Dockerfile`
   - **Port**: `8000`

3. **Configura las Variables de Entorno:**

   En la sección **Environment Variables**, añade:

   ```
   API_KEY=tu-clave-super-secreta
   OPENAI_API_KEY=sk-tu-openai-api-key
   OPENAI_BASE_URL=https://api.openai.com/v1
   LLM_MODEL=gpt-4o-mini
   VISION_MODEL=gpt-4o
   EMBEDDING_MODEL=text-embedding-3-large
   EMBEDDING_DIM=3072
   PARSER=mineru
   PARSE_METHOD=auto
   ENABLE_IMAGE_PROCESSING=true
   ENABLE_TABLE_PROCESSING=true
   ENABLE_EQUATION_PROCESSING=true
   ```

4. **Configura Volúmenes Persistentes:**

   En **Volumes**, crea:
   - `/app/rag_storage` → Para datos del RAG
   - `/app/output` → Para documentos procesados
   - `/app/uploads` → Para archivos subidos

5. **Despliega:**
   - Click en **Deploy**
   - Espera 3-5 minutos para que se construya la imagen
   - Verifica el estado en **Logs**

6. **Obtén la URL:**
   - Easypanel te dará una URL pública: `https://raganything-api.tu-dominio.com`
   - O configura un dominio personalizado

### Opción 2: Desde Docker Hub

Si prefieres construir la imagen localmente y subirla:

```bash
# Construir imagen
docker build -t tu-usuario/raganything-api:latest .

# Push a Docker Hub
docker push tu-usuario/raganything-api:latest

# En Easypanel, usa: From Docker Image
# Image: tu-usuario/raganything-api:latest
```

---

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Sin autenticación requerida**

```bash
curl https://tu-api.com/health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "message": "RAG-Anything API is running",
  "rag_initialized": true
}
```

---

### 2. Upload Document

**Endpoint:** `POST /upload`

**Headers:**
- `X-API-Key`: Tu API key configurada

**Body:** `multipart/form-data`
- `file`: Archivo a subir

**Formatos soportados:**
- PDF: `.pdf`
- Office: `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`
- Imágenes: `.jpg`, `.png`, `.bmp`, `.tiff`, `.gif`, `.webp`
- Texto: `.txt`, `.md`

**Ejemplo con curl:**
```bash
curl -X POST https://tu-api.com/upload \
  -H "X-API-Key: tu-clave-secreta" \
  -F "file=@documento.pdf"
```

**Respuesta:**
```json
{
  "success": true,
  "doc_id": "a1b2c3d4e5f6",
  "file_name": "documento.pdf",
  "message": "Document processed successfully",
  "timestamp": "2025-01-15T10:30:00.000Z"
}
```

---

### 3. Query Documents

**Endpoint:** `POST /query`

**Headers:**
- `X-API-Key`: Tu API key
- `Content-Type`: `application/json`

**Body:**
```json
{
  "query": "¿Cuáles son los principales hallazgos?",
  "file_name": "documento.pdf",  // Opcional: buscar solo en este archivo
  "mode": "mix",                 // Opcional: mix (default), hybrid, local, global, naive
  "vlm_enhanced": true           // Opcional: analizar imágenes con VLM
}
```

**Parámetros:**
- `query` (requerido): Pregunta o búsqueda
- `file_name` (opcional): Nombre del archivo para filtrar. Si no se especifica, busca en todos
- `mode` (opcional): Modo de búsqueda
  - `mix` (default): Combina todos los métodos de búsqueda
  - `hybrid`: Combina búsqueda local y global
  - `local`: Búsqueda en chunks específicos
  - `global`: Búsqueda en el grafo completo
  - `naive`: Búsqueda simple por vector
- `vlm_enhanced` (opcional): Usar modelo de visión para analizar imágenes

**Ejemplo - Buscar en documento específico:**
```bash
curl -X POST https://tu-api.com/query \
  -H "X-API-Key: tu-clave-secreta" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué dice sobre ventas?",
    "file_name": "reporte-trimestral.pdf"
  }'
```

**Ejemplo - Buscar en todos los documentos:**
```bash
curl -X POST https://tu-api.com/query \
  -H "X-API-Key: tu-clave-secreta" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Cuál es el presupuesto total?"
  }'
```

**Respuesta:**
```json
{
  "query": "¿Qué dice sobre ventas?",
  "result": "Según el documento reporte-trimestral.pdf, las ventas del Q1 2025 alcanzaron $1.2M, un incremento del 15% respecto al trimestre anterior...",
  "file_name": "reporte-trimestral.pdf",
  "mode": "hybrid",
  "timestamp": "2025-01-15T10:35:00.000Z"
}
```

---

### 4. List Documents

**Endpoint:** `GET /documents`

**Headers:**
- `X-API-Key`: Tu API key

**Ejemplo:**
```bash
curl https://tu-api.com/documents \
  -H "X-API-Key: tu-clave-secreta"
```

**Respuesta:**
```json
{
  "total": 3,
  "documents": [
    {
      "doc_id": "a1b2c3d4e5f6",
      "file_name": "reporte-trimestral.pdf",
      "file_size": 2048576,
      "upload_timestamp": "2025-01-15T10:30:00.000Z",
      "status": "processed"
    },
    {
      "doc_id": "x7y8z9w0v1u2",
      "file_name": "presentacion.pptx",
      "file_size": 5242880,
      "upload_timestamp": "2025-01-14T15:20:00.000Z",
      "status": "processed"
    }
  ]
}
```

---

### 5. Delete Document

**Endpoint:** `DELETE /documents/{doc_id}`

**Headers:**
- `X-API-Key`: Tu API key

**Ejemplo:**
```bash
curl -X DELETE https://tu-api.com/documents/a1b2c3d4e5f6 \
  -H "X-API-Key: tu-clave-secreta"
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Document removed from metadata (knowledge graph data persists)",
  "doc_id": "a1b2c3d4e5f6"
}
```

**Nota:** El documento se elimina de la metadata, pero los datos permanecen en el grafo de conocimiento.

---

## Integración con n8n

### Workflow Ejemplo: Procesar y Consultar Documentos

#### 1. Subir Documento desde n8n

**Node:** HTTP Request

**Configuración:**
- **Method:** POST
- **URL:** `https://tu-api.com/upload`
- **Authentication:** None
- **Headers:**
  ```json
  {
    "X-API-Key": "tu-clave-secreta"
  }
  ```
- **Body Content Type:** Form-Data
- **Send Body:** Yes
- **Specify Body:** Using Fields
- **Body Parameters:**
  - **Name:** `file`
  - **Type:** File
  - **Input Data Field Name:** `binary` (o el nombre de tu archivo en n8n)

**Respuesta:** Guarda el `doc_id` y `file_name` para futuras queries.

---

#### 2. Hacer Consulta a Documento Específico

**Node:** HTTP Request

**Configuración:**
- **Method:** POST
- **URL:** `https://tu-api.com/query`
- **Authentication:** None
- **Headers:**
  ```json
  {
    "X-API-Key": "tu-clave-secreta",
    "Content-Type": "application/json"
  }
  ```
- **Body Content Type:** JSON
- **Send Body:** Yes
- **Specify Body:** Using JSON
- **JSON Body:**
  ```json
  {
    "query": "{{ $json.pregunta }}",
    "file_name": "{{ $json.nombre_archivo }}",
    "mode": "hybrid"
  }
  ```

---

#### 3. Consulta Global en Todos los Documentos

Similar al anterior, pero **sin** `file_name`:

```json
{
  "query": "{{ $json.pregunta }}",
  "mode": "hybrid"
}
```

---

#### 4. Workflow Completo: Chat con Documentos

```
[Trigger: Webhook]
    → Recibe pregunta del usuario

[HTTP Request: Query API]
    → POST /query con la pregunta

[Code Node: Format Response]
    → Formatea la respuesta

[Respond to Webhook]
    → Devuelve respuesta al usuario
```

**Ejemplo de Body en Code Node:**
```javascript
// Extraer solo el resultado
const result = $input.item.json.result;

return {
  json: {
    respuesta: result,
    timestamp: new Date().toISOString()
  }
};
```

---

#### 5. Workflow: Procesamiento Automático de Documentos

```
[Trigger: Google Drive - New File]
    → Detecta nuevo archivo en carpeta

[HTTP Request: Upload to RAG]
    → POST /upload con el archivo

[Set Node: Save Metadata]
    → Guarda doc_id y file_name

[Slack/Email: Notify]
    → Notifica que el documento fue procesado
```

---

### Ejemplo n8n - AI Agent con RAG

**Setup:**

1. **Node: Chat Trigger**
   - Inicia conversación con usuario

2. **Node: AI Agent**
   - **Model:** GPT-4 (o tu preferencia)
   - **Tools:**
     - Tool 1: HTTP Request to `/query` (buscar en documentos)
     - Tool 2: HTTP Request to `/upload` (subir documentos)

3. **Tool Configuration - Query Documents:**
   ```json
   {
     "name": "search_documents",
     "description": "Busca información en los documentos procesados. Usa file_name para buscar en un documento específico.",
     "method": "POST",
     "url": "https://tu-api.com/query",
     "headers": {
       "X-API-Key": "tu-clave-secreta"
     },
     "body": {
       "query": "{{ $json.pregunta }}",
       "file_name": "{{ $json.archivo || undefined }}"
     }
   }
   ```

**Uso:**
- Usuario: "¿Qué dice el reporte-Q1.pdf sobre ventas?"
- Agent: Usa la tool `search_documents` con `file_name: "reporte-Q1.pdf"`
- Agent: Devuelve respuesta basada en el documento

---

## Variables de Entorno

### Variables Requeridas

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `API_KEY` | Clave para autenticar requests | `mi-clave-secreta-123` |
| `OPENAI_API_KEY` | API key de OpenAI | `sk-...` |

### Variables Opcionales

#### Configuración de Modelos

| Variable | Descripción | Default |
|----------|-------------|---------|
| `OPENAI_BASE_URL` | Base URL de OpenAI API | `https://api.openai.com/v1` |
| `LLM_MODEL` | Modelo LLM para texto | `gpt-4o-mini` |
| `VISION_MODEL` | Modelo para visión | `gpt-4o` |
| `EMBEDDING_MODEL` | Modelo de embeddings | `text-embedding-3-large` |
| `EMBEDDING_DIM` | Dimensión de embeddings | `3072` |

#### Configuración del Servidor

| Variable | Descripción | Default |
|----------|-------------|---------|
| `PORT` | Puerto del servidor | `8000` |
| `HOST` | Host binding | `0.0.0.0` |
| `PARSER` | Parser a usar (mineru o docling) | `mineru` |
| `PARSE_METHOD` | Método de parsing (auto, ocr, txt) | `auto` |

#### Directorios

| Variable | Descripción | Default |
|----------|-------------|---------|
| `WORKING_DIR` | Directorio de trabajo RAG | `/app/rag_storage` |
| `OUTPUT_DIR` | Directorio de documentos procesados | `/app/output` |
| `UPLOAD_DIR` | Directorio de archivos subidos | `/app/uploads` |

#### LightRAG - Configuración LLM

| Variable | Descripción | Default |
|----------|-------------|---------|
| `ENABLE_LLM_CACHE` | Habilitar cache de LLM | `true` |
| `ENABLE_LLM_CACHE_FOR_EXTRACT` | Cache para extracción | `true` |
| `TIMEOUT` | Timeout en segundos para LLM | `240` |
| `TEMPERATURE` | Temperatura del modelo (0-1) | `0` |
| `MAX_ASYNC` | Requests concurrentes a LLM | `4` |
| `MAX_TOKENS` | Máx tokens enviados al LLM | `32768` |

#### LightRAG - Configuración de Búsqueda

| Variable | Descripción | Default |
|----------|-------------|---------|
| `HISTORY_TURNS` | Turnos de historial en queries | `3` |
| `COSINE_THRESHOLD` | Umbral de similitud coseno | `0.2` |
| `TOP_K` | Top K resultados a recuperar | `60` |
| `MAX_TOKEN_TEXT_CHUNK` | Máx tokens por chunk de texto | `4000` |
| `MAX_TOKEN_RELATION_DESC` | Máx tokens descripción relación | `4000` |
| `MAX_TOKEN_ENTITY_DESC` | Máx tokens descripción entidad | `4000` |

#### LightRAG - Entidades y Relaciones

| Variable | Descripción | Default |
|----------|-------------|---------|
| `SUMMARY_LANGUAGE` | Idioma para resúmenes (English, Spanish, etc.) | `English` |
| `FORCE_LLM_SUMMARY_ON_MERGE` | Nº duplicados para re-summarize | `6` |
| `MAX_TOKEN_SUMMARY` | Máx tokens en resúmenes | `500` |

#### LightRAG - Procesamiento de Documentos

| Variable | Descripción | Default |
|----------|-------------|---------|
| `MAX_PARALLEL_INSERT` | Documentos procesados en paralelo | `2` |
| `CHUNK_SIZE` | Tamaño de chunks (tokens) | `1200` |
| `CHUNK_OVERLAP_SIZE` | Overlap entre chunks (tokens) | `100` |

#### LightRAG - Embeddings

| Variable | Descripción | Default |
|----------|-------------|---------|
| `EMBEDDING_BATCH_NUM` | Chunks por batch de embedding | `32` |
| `EMBEDDING_FUNC_MAX_ASYNC` | Requests concurrentes embedding | `16` |

#### LightRAG - Grafo

| Variable | Descripción | Default |
|----------|-------------|---------|
| `MAX_GRAPH_NODES` | Máximo nodos retornados del grafo | `1000` |

#### Logging

| Variable | Descripción | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Nivel de logging (INFO, DEBUG, etc.) | `INFO` |
| `VERBOSE` | Modo verbose | `false` |
| `LOG_MAX_BYTES` | Tamaño máximo de log file | `10485760` |
| `LOG_BACKUP_COUNT` | Archivos de backup de logs | `5` |

### Recomendaciones de Configuración

**Para mejor rendimiento:**
```env
MAX_ASYNC=8                    # Más requests concurrentes
EMBEDDING_FUNC_MAX_ASYNC=32   # Más embeddings en paralelo
MAX_PARALLEL_INSERT=4         # Más documentos en paralelo
```

**Para ahorrar costos:**
```env
ENABLE_LLM_CACHE=true         # Cachear responses
CHUNK_SIZE=800                # Chunks más pequeños
TOP_K=30                      # Menos resultados
```

**Para documentos grandes:**
```env
CHUNK_SIZE=1500               # Chunks más grandes
CHUNK_OVERLAP_SIZE=200        # Más overlap
MAX_TOKEN_TEXT_CHUNK=6000     # Más tokens por chunk
```

**Para mejor precisión:**
```env
COSINE_THRESHOLD=0.3          # Umbral más alto
TOP_K=100                     # Más resultados
FORCE_LLM_SUMMARY_ON_MERGE=3  # Re-summarize antes
```

---

## Ejemplos de Uso

### Script Python - Cliente de la API

```python
import requests

API_URL = "https://tu-api.com"
API_KEY = "tu-clave-secreta"

headers = {
    "X-API-Key": API_KEY
}

# 1. Subir documento
with open("documento.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{API_URL}/upload",
        headers=headers,
        files=files
    )
    print("Upload:", response.json())

# 2. Hacer query
query_data = {
    "query": "¿Cuáles son los hallazgos principales?",
    "file_name": "documento.pdf"
}
response = requests.post(
    f"{API_URL}/query",
    headers={**headers, "Content-Type": "application/json"},
    json=query_data
)
print("Query:", response.json())

# 3. Listar documentos
response = requests.get(
    f"{API_URL}/documents",
    headers=headers
)
print("Documents:", response.json())
```

---

### JavaScript/TypeScript - Cliente

```javascript
const API_URL = "https://tu-api.com";
const API_KEY = "tu-clave-secreta";

// Subir documento
async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY
    },
    body: formData
  });

  return await response.json();
}

// Hacer query
async function queryDocuments(query, fileName = null) {
  const body = {
    query: query,
    ...(fileName && { file_name: fileName })
  };

  const response = await fetch(`${API_URL}/query`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });

  return await response.json();
}

// Uso
const result = await queryDocuments("¿Qué dice sobre ventas?", "reporte.pdf");
console.log(result.result);
```

---

## Troubleshooting

### Error: "OPENAI_API_KEY not set"

**Causa:** Falta la API key de OpenAI.

**Solución:**
```bash
# En .env o variables de entorno de Easypanel
OPENAI_API_KEY=sk-tu-key-aqui
```

---

### Error: "Invalid API Key" (401)

**Causa:** El header `X-API-Key` no coincide con `API_KEY` configurada.

**Solución:**
- Verifica que usas el header correcto: `X-API-Key`
- Verifica que el valor coincide con tu `.env`

---

### Error: "RAG instance not initialized" (503)

**Causa:** El servidor no pudo inicializar RAGAnything.

**Solución:**
1. Verifica los logs del contenedor:
   ```bash
   docker logs raganything-api
   ```
2. Verifica que `OPENAI_API_KEY` es válida
3. Verifica conexión a OpenAI API

---

### Documento no se procesa (Office docs)

**Causa:** LibreOffice no está instalado o no funciona.

**Solución:**
- El Dockerfile ya incluye LibreOffice
- Verifica logs: `LibreOffice is installed`
- Si usas imagen personalizada, asegúrate de instalar libreoffice

---

### Queries muy lentas

**Causa:** Procesamiento de imágenes con VLM.

**Solución:**
- Desactiva VLM si no es necesario: `"vlm_enhanced": false`
- Usa modelo LLM más rápido: `LLM_MODEL=gpt-4o-mini`

---

### Out of Memory (OOM)

**Causa:** Documentos muy grandes o muchos archivos.

**Solución:**
- Aumenta memoria en docker-compose.yml:
  ```yaml
  deploy:
    resources:
      limits:
        memory: 8G
  ```
- En Easypanel: Aumenta recursos del contenedor

---

## Recursos Adicionales

- **Documentación RAG-Anything:** [README.md](README.md)
- **LightRAG:** https://github.com/HKUDS/LightRAG
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **n8n Docs:** https://docs.n8n.io
- **Easypanel Docs:** https://easypanel.io/docs

---

## Soporte

Para issues o preguntas:
- GitHub Issues: https://github.com/HKUDS/RAG-Anything/issues
- Discord: https://discord.gg/yF2MmDJyGJ

---

**¡Disfruta de tu servidor RAG-Anything! 🚀**
