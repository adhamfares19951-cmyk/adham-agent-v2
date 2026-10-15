# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install system dependencies (git for GitHub engine, curl, sqlite3, build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    sqlite3 \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Gaza

# Entrypoint runs the self-healing watchdog supervisor
CMD ["python", "watchdog.py"]
