# RallyCal Production Dockerfile with Multi-stage Build
# Optimized for minimal image size and security best practices

# ==============================================================================
# Build Stage: Install dependencies and build the application
# ==============================================================================
FROM python:3.13-slim as builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for building
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install system dependencies needed for building
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies in virtual environment
RUN uv venv /opt/venv \
    && uv pip install --python /opt/venv/bin/python -r pyproject.toml

# Copy source code
COPY src/ src/
COPY main.py ./

# Create production configuration directory
RUN mkdir -p /app/config

# Change ownership to appuser
RUN chown -R appuser:appuser /app /opt/venv
USER appuser

# ==============================================================================
# Production Stage: Minimal runtime image
# ==============================================================================
FROM python:3.13-slim as production

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    RALLYCAL_ENVIRONMENT=production \
    RALLYCAL_LOG_LEVEL=INFO \
    RALLYCAL_HOST=0.0.0.0 \
    RALLYCAL_PORT=8000

# Install only runtime system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for runtime
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser \
    && mkdir -p /app/logs /app/config \
    && chown -R appuser:appuser /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv

# Copy application code from builder stage
COPY --from=builder --chown=appuser:appuser /app/src /app/src
COPY --from=builder --chown=appuser:appuser /app/main.py /app/

# Switch to non-root user
USER appuser
WORKDIR /app

# Create startup script
RUN cat > /app/start.sh << 'EOF'
#!/bin/bash
set -e

# Wait for database if DATABASE_URL is provided
if [ -n "$DATABASE_URL" ] && [ "$DATABASE_URL" != "sqlite:///./rallycal.db" ]; then
    echo "Waiting for database connection..."
    python -c "
import asyncio
import sys
from src.rallycal.database.engine import db_manager

async def check_db():
    try:
        await db_manager.initialize()
        connected = await db_manager.check_connection()
        if connected:
            print('Database connection successful')
            return 0
        else:
            print('Database connection failed')
            return 1
    except Exception as e:
        print(f'Database connection error: {e}')
        return 1
    finally:
        await db_manager.close()

sys.exit(asyncio.run(check_db()))
    "
    if [ $? -ne 0 ]; then
        echo "Failed to connect to database"
        exit 1
    fi
fi

# Run database migrations
echo "Running database migrations..."
python -c "
import asyncio
from src.rallycal.database.engine import db_manager

async def migrate():
    try:
        await db_manager.initialize()
        await db_manager.create_tables()
        print('Database migrations completed')
    except Exception as e:
        print(f'Migration error: {e}')
        raise
    finally:
        await db_manager.close()

asyncio.run(migrate())
"

# Start the application
echo "Starting RallyCal application..."
exec uvicorn src.rallycal.api.main:app \
    --host "$RALLYCAL_HOST" \
    --port "$RALLYCAL_PORT" \
    --workers 1 \
    --log-level info \
    --access-log \
    --loop uvloop \
    --http httptools
EOF

RUN chmod +x /app/start.sh

# Health check script
RUN cat > /app/healthcheck.py << 'EOF'
#!/usr/bin/env python3
"""Health check script for Docker container."""
import asyncio
import sys
from urllib.parse import urljoin

import httpx


async def health_check():
    """Perform health check against the application."""
    base_url = f"http://localhost:{os.environ.get('RALLYCAL_PORT', 8000)}"
    health_url = urljoin(base_url, "/health")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(health_url)
            if response.status_code == 200:
                print("Health check passed")
                return 0
            else:
                print(f"Health check failed with status: {response.status_code}")
                return 1
    except Exception as e:
        print(f"Health check error: {e}")
        return 1


if __name__ == "__main__":
    import os
    sys.exit(asyncio.run(health_check()))
EOF

RUN chmod +x /app/healthcheck.py

# Expose port
EXPOSE 8000

# Configure Docker health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /app/healthcheck.py

# Set volume for persistent data
VOLUME ["/app/logs", "/app/config"]

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]

# Default command
CMD ["/app/start.sh"]

# Metadata labels
LABEL maintainer="RallyCal Team" \
      description="Family sports calendar aggregator" \
      version="0.1.0" \
      org.opencontainers.image.title="RallyCal" \
      org.opencontainers.image.description="Family sports calendar aggregator that combines multiple iCal/ICS feeds" \
      org.opencontainers.image.vendor="RallyCal Team" \
      org.opencontainers.image.licenses="MIT"