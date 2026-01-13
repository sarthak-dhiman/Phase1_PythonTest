# Multi-stage Dockerfile: build wheels in a builder stage, install only runtime deps in final image

FROM python:3.11-slim AS builder

# keep python output unbuffered and avoid .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app 
 

# Install build-time packages needed to compile wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libssl-dev \
        libffi-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Upgrade pip and build wheels into /wheels
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip wheel --wheel-dir=/wheels -r /app/requirements.txt

# Final slim image: no build tools
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install minimal runtime system libs (if any packages require them at runtime)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libssl-dev \
        libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels from builder and install them without network access
COPY --from=builder /wheels /wheels
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools && \
    pip install --no-index --find-links=/wheels -r /app/requirements.txt --no-cache-dir && \
    rm -rf /wheels

# Copy project code (after deps installed to maximize cache reuse)
COPY . /app

# Expose port only as documentation; change if not needed
EXPOSE 8000

# Default behaviour: run API server if API_SERVER env var is set to '1', else run CLI
ENV API_SERVER=0
CMD ["/bin/sh", "-c", "if [ \"$API_SERVER\" = \"1\" ]; then exec uvicorn api_server:app --host 0.0.0.0 --port 8000; else exec python -u base_processor.py; fi"]
