# 🚀 Inicio Rápido - RAG-Anything API

Guía de 5 minutos para tener tu API RAG funcionando.

## Opción 1: Docker Compose (Local)

### 1. Clona el repositorio
```bash
git clone https://github.com/HKUDS/RAG-Anything.git
cd RAG-Anything
```

### 2. Configura variables de entorno
```bash
# Copia el template
cp .env.docker .env

# Edita y añade tu OpenAI API key
nano .env
```

Cambia estas líneas en `.env`:
```env
API_KEY=mi-clave-super-secreta-123
OPENAI_API_KEY=sk-tu-openai-key-aqui
```

**💡 Tip:** Para ajustar rendimiento, costos, o idioma, consulta **[ENV_VARIABLES_REFERENCE.md](ENV_VARIABLES_REFERENCE.md)**

### 3. Inicia el servidor
```bash
docker-compose up -d
```

### 4. Verifica que funciona
```bash
curl http://localhost:8000/health
```

Deberías ver:
```json
{"status":"healthy","message":"RAG-Anything API is running","rag_initialized":true}
```

### 5. Prueba la API
```bash
# Sube un documento
curl -X POST http://localhost:8000/upload \
  -H "X-API-Key: mi-clave-super-secreta-123" \
  -F "file=@tu-documento.pdf"

# Haz una consulta
curl -X POST http://localhost:8000/query \
  -H "X-API-Key: mi-clave-super-secreta-123" \
  -H "Content-Type: application/json" \
  -d '{"query": "¿De qué trata este documento?"}'
```

---

## Opción 2: Easypanel

### 1. Sube tu código a GitHub
```bash
git add .
git commit -m "Add RAG-Anything API"
git push origin main
```

### 2. En Easypanel

1. **Create Project** → **Docker** → **From Git Repository**

2. Conecta tu repositorio

3. **Configuración:**
   - Port: `8000`
   - Dockerfile path: `Dockerfile`

4. **Variables de entorno (añade estas):**
   ```
   API_KEY=tu-clave-secreta
   OPENAI_API_KEY=sk-tu-openai-key
   ```

5. **Deploy**

6. Espera 3-5 minutos

7. **Obtén tu URL:** `https://raganything-api.tu-dominio.com`

### 3. Prueba tu API
```bash
# Reemplaza con tu URL de Easypanel
API_URL="https://raganything-api.tu-dominio.com"

curl $API_URL/health
```

---

## Uso con n8n

### Workflow Simple: Chat con Documentos

1. **HTTP Request Node - Upload:**
   - Method: `POST`
   - URL: `https://tu-api.com/upload`
   - Headers: `X-API-Key: tu-clave`
   - Body: Form-Data con tu archivo

2. **HTTP Request Node - Query:**
   - Method: `POST`
   - URL: `https://tu-api.com/query`
   - Headers: `X-API-Key: tu-clave`, `Content-Type: application/json`
   - Body JSON:
     ```json
     {
       "query": "{{ $json.pregunta }}",
       "file_name": "documento.pdf"
     }
     ```

### AI Agent Setup

1. Añade **Tool: HTTP Request**
2. Configura:
   - Name: `search_documents`
   - Description: "Busca información en documentos"
   - URL: `https://tu-api.com/query`
   - Headers: `X-API-Key: tu-clave`

3. El agente ahora puede buscar en tus documentos automáticamente!

---

## Comandos Útiles

```bash
# Ver logs
docker-compose logs -f

# Reiniciar
docker-compose restart

# Parar
docker-compose down

# Limpiar todo
docker-compose down -v

# Ejecutar tests
python test_api.py
```

---

## Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Verificar estado |
| `/upload` | POST | Subir documento |
| `/query` | POST | Hacer consulta |
| `/documents` | GET | Listar documentos |
| `/documents/{id}` | DELETE | Eliminar documento |

---

## Documentación Completa

Ver **[README_DOCKER.md](README_DOCKER.md)** para:
- Ejemplos detallados
- Integración con n8n
- Troubleshooting
- Configuración avanzada

---

## Soporte

- Issues: https://github.com/HKUDS/RAG-Anything/issues
- Discord: https://discord.gg/yF2MmDJyGJ

---

**¡Listo para usar! 🎉**
