#!/bin/bash

# Antigravity AI: Automated Setup Script
echo "🚀 Starting Automated Setup..."

# 1. Backend Setup
echo "🔹 Setting up Python Backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# 2. Frontend Setup
echo "🔹 Setting up React Frontend..."
cd frontend
npm install
cd ..

# 3. Ollama Models
echo "🔹 Pulling Required Ollama Models..."
ollama pull gemma3:4b
ollama pull nomic-embed-text
ollama pull llava

echo "✅ Setup Complete! To start the system:"
echo "1. Terminal 1: cd backend && source venv/bin/activate && python main.py"
echo "2. Terminal 2: cd frontend && npm run dev"
