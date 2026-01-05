FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    util-linux \
    bash

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN addgroup -g 1000 controller && \
    adduser -D -u 1000 -G controller controller && \
    chown -R controller:controller /app

USER controller

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD test -f /tmp/controller-health || exit 1

# Run application
CMD ["python", "-u", "src/main.py"]
