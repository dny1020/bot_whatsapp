#!/bin/bash
# Setup script for WhatsApp Chatbot Platform

set -e

echo "🚀 Setting up WhatsApp Chatbot Platform..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your WhatsApp credentials before continuing"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Build and start services
echo "🐳 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "📋 Service URLs:"
    echo "   Backend API: http://localhost:8000"
    echo "   Webhook: http://localhost:8001"
    echo "   Health Check: http://localhost:8000/health"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Configure your WhatsApp webhook URL in Meta Developer Console"
    echo "   2. Use ngrok or similar to expose webhook: ngrok http 8001"
    echo "   3. Set webhook URL to: https://your-ngrok-url/webhook"
    echo "   4. Monitor logs: docker-compose logs -f"
    echo ""
    echo "✅ Setup complete!"
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi
