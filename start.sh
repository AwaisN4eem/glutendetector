#!/bin/bash
# Quick start script for GlutenGuard AI

echo "🌾 GlutenGuard AI - Quick Start"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Setup backend
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

echo "Downloading NLP model..."
python -m spacy download en_core_web_sm

if [ ! -f "glutenguard.db" ]; then
    echo "Generating sample data..."
    python generate_sample_data.py 42
fi

echo ""
echo "✅ Backend setup complete!"
echo ""

# Setup frontend
echo "📦 Setting up frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
fi

echo ""
echo "✅ Frontend setup complete!"
echo ""

# Instructions
echo "🚀 Ready to start!"
echo ""
echo "Open TWO terminals:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""
echo "🌟 Try uploading a food photo - it's amazing!"

