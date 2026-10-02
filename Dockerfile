# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Prevent Python from writing bytecode and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install minimal runtime utilities (curl for container health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Security Hardening: Create dedicated unprivileged system user and group
RUN groupadd -g 10001 edgestore && \
    useradd -u 10001 -g edgestore -m -s /bin/bash edgestore

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code and pre-built frozen frontend
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/dist/

# Prepare persistent volume mount directories with strict permissions
RUN mkdir -p /data/primary /data/replica /data/db && \
    chown -R edgestore:edgestore /app /data

# Default runtime environment configuration for Phase 1 Docker mode
ENV ENVIRONMENT_MODE=docker \
    HOST=0.0.0.0 \
    PORT=8000 \
    PRIMARY_STORAGE_PATH=/data/primary \
    REPLICA_STORAGE_PATH=/data/replica \
    DATABASE_URL=sqlite:////data/db/edgestore.db

EXPOSE 8000

# Run container as non-root user (Principle of Least Privilege)
USER edgestore

# Health Check validation
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
