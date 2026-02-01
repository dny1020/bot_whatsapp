FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/
COPY app.py /app/


# Create required directories
RUN mkdir -p /app/data/vector_store /app/config

# Set Python path       
ENV PYTHONPATH=/app

# Expose unified port
EXPOSE 8000

# Run unified application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]
