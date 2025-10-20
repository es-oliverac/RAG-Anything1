#!/bin/bash
set -e

echo "========================================"
echo "  RAG-Anything API Server"
echo "========================================"

# Validate required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable is not set!"
    echo "Please set it in your .env file or docker-compose.yml"
    exit 1
fi

# Create necessary directories
mkdir -p /app/rag_storage
mkdir -p /app/output
mkdir -p /app/uploads
mkdir -p /app/tiktoken_cache

echo "✓ Directories created"

# Check LibreOffice installation
if command -v libreoffice &> /dev/null; then
    echo "✓ LibreOffice is installed: $(libreoffice --version | head -n1)"
else
    echo "WARNING: LibreOffice not found. Office document conversion will not work."
fi

# Display configuration
echo ""
echo "Configuration:"
echo "  - LLM Model: ${LLM_MODEL:-gpt-4o-mini}"
echo "  - Vision Model: ${VISION_MODEL:-gpt-4o}"
echo "  - Embedding Model: ${EMBEDDING_MODEL:-text-embedding-3-large}"
echo "  - Parser: ${PARSER:-mineru}"
echo "  - Working Dir: ${WORKING_DIR:-/app/rag_storage}"
echo "  - Port: ${PORT:-8000}"
echo ""

# Start the FastAPI server
echo "Starting RAG-Anything API server..."
echo "========================================"

exec uvicorn api_server:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    --log-level "${LOG_LEVEL:-info}" \
    --no-access-log
