# Email Triage OpenEnv — Dockerfile
# Compatible with HuggingFace Spaces (runs as non-root user 1000)

FROM python:3.11-slim

# HF Spaces requires port 7860
EXPOSE 7860

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY email_triage/ ./email_triage/
COPY server/ ./server/

# HuggingFace Spaces runs as UID 1000
RUN useradd -m -u 1000 hfuser
USER 1000

# Environment variables
ENV PORT=7860 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start the server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
