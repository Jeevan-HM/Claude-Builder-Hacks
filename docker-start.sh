#!/bin/bash

# Docker quick start script for Claude Builder Hacks

set -e

echo "🐳 Claude Builder Hacks - Docker Quick Start"
echo "============================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker found: $(docker --version)"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo ""
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY (Claude AI)"
    echo "   - GEMINI_API_KEY (Google Gemini)"
    echo ""
    read -p "Press Enter after adding your API keys to .env..."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads
echo "✅ Directories created"

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo ""
echo "🔨 Building Docker image..."
docker build -t claude-builder-hacks .

echo ""
echo "✅ Build complete!"
echo ""
echo "🚀 Starting container..."
echo ""

# Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=claude-builder)" ]; then
    echo "Stopping existing container..."
    docker stop claude-builder 2>/dev/null || true
    docker rm claude-builder 2>/dev/null || true
fi

# Run the container
docker run -d \
  --name claude-builder \
  -p 5000:5000 \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -v "$(pwd)/uploads:/app/uploads" \
  -v "$(pwd)/project_tracker.db:/app/project_tracker.db" \
  --restart unless-stopped \
  claude-builder-hacks

echo ""
echo "✅ Container started successfully!"
echo ""
echo "📊 Container status:"
docker ps -f name=claude-builder

echo ""
echo "🎉 Application is running!"
echo ""
echo "Access the application at:"
echo "   Dashboard:   http://localhost:5000"
echo "   Onboarding:  http://localhost:5000/onboarding"
echo "   Mindmap:     http://localhost:5000/mindmap"
echo "   MCP Tester:  http://localhost:5000/mcp-tester"
echo ""
echo "Useful commands:"
echo "   View logs:    docker logs -f claude-builder"
echo "   Stop:         docker stop claude-builder"
echo "   Start:        docker start claude-builder"
echo "   Remove:       docker rm -f claude-builder"
echo ""
