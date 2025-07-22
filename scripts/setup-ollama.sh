#!/bin/bash

# Ollama Setup Script for Zundamon Mandan Demo
# This script sets up Ollama with the mistral model for the kiosk system

echo "🤖 Ollama Setup Script for Zundamon Mandan Demo"
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Start Ollama service
echo "🚀 Starting Ollama service..."
cd "$(dirname "$0")/.."
docker-compose -f docker/docker-compose.yml up -d ollama

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        break
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

if ! curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "❌ Ollama failed to start within 60 seconds"
    exit 1
fi

# Pull mistral model
echo "📥 Pulling mistral model (this may take a while)..."
docker exec kiosk-452-ollama ollama pull mistral

if [ $? -eq 0 ]; then
    echo "✅ Mistral model downloaded successfully!"
else
    echo "❌ Failed to download mistral model"
    exit 1
fi

# Test the model
echo "🧪 Testing mistral model..."
TEST_RESPONSE=$(docker exec kiosk-452-ollama ollama run mistral "こんにちは、ずんだもんなのだ！" --format json 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Mistral model is working correctly!"
else
    echo "⚠️  Model test failed, but installation completed"
fi

echo ""
echo "🎉 Ollama setup completed!"
echo ""
echo "Next steps:"
echo "1. Start all services: docker-compose -f docker/docker-compose.yml up -d"
echo "2. Access the kiosk at: http://localhost:3000"
echo "3. Try the 'ずんだもん漫談生成' button in the UI"
echo ""
echo "Available models:"
docker exec kiosk-452-ollama ollama list 2>/dev/null || echo "   (Run 'docker exec kiosk-452-ollama ollama list' to see models)"
