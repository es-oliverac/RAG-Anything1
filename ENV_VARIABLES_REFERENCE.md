# 📋 Referencia Rápida de Variables de Entorno

Guía rápida de las variables de entorno más importantes para RAG-Anything API.

---

## ✅ Variables Requeridas

Estas son **obligatorias** para que el sistema funcione:

```env
API_KEY=tu-clave-secreta-aqui
OPENAI_API_KEY=sk-tu-openai-key-aqui
```

---

## 🎯 Variables Más Importantes (Opcionales)

### Ajuste de Rendimiento

```env
# Requests concurrentes al LLM (más = más rápido, más caro)
MAX_ASYNC=4              # Default: 4, Recomendado: 4-8

# Requests concurrentes para embeddings
EMBEDDING_FUNC_MAX_ASYNC=16   # Default: 16, Recomendado: 16-32

# Documentos procesados en paralelo
MAX_PARALLEL_INSERT=2    # Default: 2, Recomendado: 2-4
```

### Ajuste de Calidad de Búsqueda

```env
# Número de resultados recuperados
TOP_K=60                 # Default: 60, Más alto = más contexto

# Umbral de similitud (0-1)
COSINE_THRESHOLD=0.2     # Default: 0.2, Más alto = más estricto

# Tamaño de chunks de texto
CHUNK_SIZE=1200          # Default: 1200, Rango: 800-1500

# Overlap entre chunks
CHUNK_OVERLAP_SIZE=100   # Default: 100, Rango: 50-200
```

### Ahorro de Costos

```env
# Cache de LLM (ahorra llamadas)
ENABLE_LLM_CACHE=true    # Default: true, Recomendado: true

# Temperatura (0 = determinista)
TEMPERATURE=0            # Default: 0, Rango: 0-1

# Usar modelo más barato
LLM_MODEL=gpt-4o-mini    # Default: gpt-4o-mini
```

### Idioma

```env
# Idioma para resúmenes y procesamiento
SUMMARY_LANGUAGE=Spanish    # Default: English
# Opciones: English, Spanish, Chinese, French, German, etc.
```

---

## 📊 Casos de Uso Comunes

### Caso 1: Máximo Rendimiento (más caro)

```env
MAX_ASYNC=8
EMBEDDING_FUNC_MAX_ASYNC=32
MAX_PARALLEL_INSERT=4
ENABLE_LLM_CACHE=true
LLM_MODEL=gpt-4o
```

**Efecto:**
- ✅ Procesamiento muy rápido
- ✅ Queries muy rápidas
- ❌ Más costoso ($$$)

---

### Caso 2: Equilibrado (recomendado)

```env
MAX_ASYNC=4
EMBEDDING_FUNC_MAX_ASYNC=16
MAX_PARALLEL_INSERT=2
ENABLE_LLM_CACHE=true
LLM_MODEL=gpt-4o-mini
CHUNK_SIZE=1200
TOP_K=60
```

**Efecto:**
- ✅ Buen rendimiento
- ✅ Costo moderado ($$)
- ✅ Buena calidad

---

### Caso 3: Ahorro Máximo (más lento)

```env
MAX_ASYNC=2
EMBEDDING_FUNC_MAX_ASYNC=8
MAX_PARALLEL_INSERT=1
ENABLE_LLM_CACHE=true
LLM_MODEL=gpt-4o-mini
CHUNK_SIZE=800
TOP_K=30
TEMPERATURE=0
```

**Efecto:**
- ✅ Bajo costo ($)
- ❌ Procesamiento más lento
- ⚠️ Calidad aceptable

---

### Caso 4: Documentos Grandes

```env
CHUNK_SIZE=1500
CHUNK_OVERLAP_SIZE=200
MAX_TOKEN_TEXT_CHUNK=6000
MAX_TOKEN_RELATION_DESC=6000
MAX_TOKEN_ENTITY_DESC=6000
TOP_K=100
```

**Efecto:**
- ✅ Mejor para PDFs largos
- ✅ Más contexto por chunk
- ⚠️ Más costoso

---

### Caso 5: Alta Precisión

```env
COSINE_THRESHOLD=0.3
TOP_K=100
FORCE_LLM_SUMMARY_ON_MERGE=3
ENABLE_LLM_CACHE_FOR_EXTRACT=true
LLM_MODEL=gpt-4o
```

**Efecto:**
- ✅ Máxima precisión
- ✅ Mejor resúmenes
- ❌ Más lento y costoso

---

## 🔧 Variables de LightRAG por Categoría

### LLM Configuration

| Variable | Qué hace | Default | Rango |
|----------|----------|---------|-------|
| `ENABLE_LLM_CACHE` | Cachear responses LLM | `true` | `true/false` |
| `TIMEOUT` | Timeout para LLM (seg) | `240` | `60-600` |
| `TEMPERATURE` | Creatividad del modelo | `0` | `0-1` |
| `MAX_ASYNC` | Requests concurrentes | `4` | `1-16` |
| `MAX_TOKENS` | Max tokens al LLM | `32768` | `4096-128000` |

### Query Settings

| Variable | Qué hace | Default | Rango |
|----------|----------|---------|-------|
| `TOP_K` | Resultados recuperados | `60` | `10-200` |
| `COSINE_THRESHOLD` | Umbral similitud | `0.2` | `0.1-0.5` |
| `CHUNK_SIZE` | Tamaño chunks (tokens) | `1200` | `500-2000` |
| `CHUNK_OVERLAP_SIZE` | Overlap chunks | `100` | `50-300` |

### Processing

| Variable | Qué hace | Default | Rango |
|----------|----------|---------|-------|
| `MAX_PARALLEL_INSERT` | Docs en paralelo | `2` | `1-8` |
| `SUMMARY_LANGUAGE` | Idioma resúmenes | `English` | Cualquier idioma |

### Embeddings

| Variable | Qué hace | Default | Rango |
|----------|----------|---------|-------|
| `EMBEDDING_BATCH_NUM` | Chunks por batch | `32` | `8-128` |
| `EMBEDDING_FUNC_MAX_ASYNC` | Requests concurrentes | `16` | `4-64` |

---

## 💡 Tips Prácticos

### 1. Empezar con Defaults
```env
# Solo configurar lo mínimo
API_KEY=tu-clave
OPENAI_API_KEY=sk-...
```
Los defaults son buenos para empezar.

### 2. Monitorear Costos
- Habilita `ENABLE_LLM_CACHE=true` siempre
- Usa `gpt-4o-mini` en lugar de `gpt-4o`
- Reduce `TOP_K` si no necesitas tanto contexto

### 3. Optimizar para tu Caso
- **Documentos cortos** → `CHUNK_SIZE=800`
- **Documentos largos** → `CHUNK_SIZE=1500`
- **Búsqueda rápida** → `TOP_K=30`
- **Búsqueda exhaustiva** → `TOP_K=100`

### 4. Español vs Inglés
```env
# Para documentos en español
SUMMARY_LANGUAGE=Spanish
LLM_MODEL=gpt-4o-mini  # Soporta bien español
```

### 5. Debugging
```env
LOG_LEVEL=DEBUG
VERBOSE=true
```
Útil para troubleshooting.

---

## 📚 Documentación Completa

Para la lista completa de **todas las variables** con descripciones detalladas:

👉 **[README_DOCKER.md - Sección Variables de Entorno](README_DOCKER.md#variables-de-entorno)**

---

## 🆘 Problemas Comunes

### "Muy lento procesando documentos"
```env
MAX_PARALLEL_INSERT=4        # Aumentar
EMBEDDING_FUNC_MAX_ASYNC=32  # Aumentar
```

### "Queries devuelven poco contexto"
```env
TOP_K=100                    # Aumentar
COSINE_THRESHOLD=0.15        # Reducir
```

### "Costo muy alto"
```env
ENABLE_LLM_CACHE=true       # Asegurar
LLM_MODEL=gpt-4o-mini       # Modelo más barato
TOP_K=30                    # Reducir
CHUNK_SIZE=800              # Reducir
```

### "Resultados imprecisos"
```env
COSINE_THRESHOLD=0.3        # Aumentar
TOP_K=100                   # Aumentar
LLM_MODEL=gpt-4o            # Modelo mejor
```

---

## 🔗 Links Útiles

- **Archivo .env.docker de ejemplo:** `.env.docker`
- **Documentación completa:** [README_DOCKER.md](README_DOCKER.md)
- **Despliegue rápido:** [QUICKSTART.md](QUICKSTART.md)

---

**Última actualización:** 2025-01-15
