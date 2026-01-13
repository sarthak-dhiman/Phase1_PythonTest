FROM python:3.11-slim

# Keep python output unbuffered and avoid .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system packages needed to compile wheels for some packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libssl-dev \
        libffi-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements (corrected filename)
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install python deps
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install -r /app/requirements.txt

# Copy project code
COPY . /app

# Typical port for FastAPI; change if not needed
EXPOSE 8000

# Default command — run base_processor.py
CMD ["python", "-u", "base_processor.py"]
