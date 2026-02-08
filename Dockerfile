# CORAL Hub Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY coral/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy CORAL hub code
COPY coral/ /app/coral/
COPY config.yaml /app/
COPY config_loader.py /app/
COPY coral_checker.py /app/
COPY coral_integration/ /app/coral_integration/
COPY logos/ /app/logos/

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5002/api/health', timeout=2)" || exit 1

# Run application
WORKDIR /app/coral
CMD ["python", "app.py"]
