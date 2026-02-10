FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY app.py .

# Dirs para volumes (config/, docs/ se montan desde docker-compose)
RUN mkdir -p /app/data /app/logs /app/config /app/docs

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
