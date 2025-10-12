# Multi-stage production Dockerfile for crypto-news-pipe
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash --uid 1000 app

# Set working directory
WORKDIR /app

# Build stage - install dependencies
FROM base as builder

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash --uid 1000 app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=app:app . .

# Create necessary directories and files
RUN mkdir -p /app/data /app/logs /app/image && \
    touch /app/data/posted.json && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Set environment variables
ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV POSTED_FILE=/app/data/posted.json
ENV IMAGE_FOLDER=/app/image

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys, os; sys.exit(0 if os.path.exists('/app/main.py') else 1)"

# Expose port for monitoring (optional)
EXPOSE 8000

# Default command
CMD ["python", "main.py"]
