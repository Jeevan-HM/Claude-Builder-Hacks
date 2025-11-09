#!/bin/bash

# Quick start script for Claude Builder Hacks
# This script helps you set up and run the application

set -e

echo "🚀 Claude Builder Hacks - Quick Start"
echo "======================================"
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
    echo "Get your keys from:"
    echo "   Claude: https://console.anthropic.com/"
    echo "   Gemini: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Press Enter after adding your API keys to .env..."
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads
echo "✅ Directories created"

# Initialize database
echo "🗄️  Initializing database..."
if [ ! -f "project_tracker.db" ]; then
    echo "Creating new database..."
else
    echo "Database already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎉 Starting the application..."
echo ""
echo "Access the application at:"
echo "   Dashboard:   http://localhost:5000"
echo "   Onboarding:  http://localhost:5000/onboarding"
echo "   Mindmap:     http://localhost:5000/mindmap"
echo "   MCP Tester:  http://localhost:5000/mcp-tester"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the application
python app.py
