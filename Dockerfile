# Multi-stage Dockerfile for RAG-Anything API Server
# Optimized for CPU-only deployment with MinerU parser

# Stage 1: Builder
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY requirements-api.txt /tmp/
COPY requirements.txt /tmp/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements-api.txt

# Stage 2: Runtime
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies and LibreOffice
RUN apt-get update && apt-get install -y --no-install-recommends \
    # LibreOffice for Office document conversion
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    # System utilities
    curl \
    ca-certificates \
    # Image processing libraries
    libgl1-mesa-glx \
    libglib2.0-0 \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash raguser && \
    mkdir -p /app /app/rag_storage /app/output /app/uploads /app/tiktoken_cache && \
    chown -R raguser:raguser /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=raguser:raguser . /app/

# Copy and make start script executable
COPY --chown=raguser:raguser start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Switch to non-root user
USER raguser

# Pre-download tiktoken models (run as user)
RUN python -c "import tiktoken; tiktoken.get_encoding('cl100k_base'); tiktoken.get_encoding('o200k_base')" || true

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["/app/start.sh"]
