# Use official slim Python 3.12 image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc files & buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list and install
COPY config.py main.py orchestrator.py tools.py logger.py reporter.py benchmark.py /app/
COPY agents /app/agents/
COPY tests /app/tests/

RUN pip install --no-cache-dir google-genai pytest

# Entrypoint to run main CLI
ENTRYPOINT ["python", "main.py"]
