# Multi-stage / Production Dockerfile for HealthBridge AI
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system dependencies including git and git-lfs for model verification
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    git-lfs \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Initialize git lfs
RUN git-lfs install

WORKDIR /app

# Install Python dependencies first for caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Ensure upload directory exists
RUN mkdir -p /app/uploads/prescriptions

# Expose port (standard 8000, dynamically overridden by cloud providers via $PORT)
EXPOSE 8000

# Production start command (uses shell form to properly expand $PORT)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
