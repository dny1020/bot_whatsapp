FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies optimized for CPU
# 1. Install torch-cpu specifically (much smaller than standard torch)
# 2. Install the rest of requirements
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Copy application code
COPY src/ /app/src/
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/
COPY app.py /app/
COPY init_db.py /app/

# Create required directories
RUN mkdir -p /app/logs /app/data/vector_store

# Set Python path       
ENV PYTHONPATH=/app

# Expose unified port
EXPOSE 8000

# Run unified application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
