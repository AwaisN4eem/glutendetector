#!/bin/bash
# Linux/Mac script to start GlutenGuard AI with Docker

echo "========================================"
echo "  GlutenGuard AI - Docker Launcher"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "[OK] Docker is running"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[WARNING] .env file not found!"
    echo "Creating .env from template..."
    echo ""
    cat > .env << 'EOF'
# GlutenGuard AI - Environment Variables

# Backend Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
DATABASE_URL=sqlite:///./glutenguard.db

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:80

# AI Services (Optional - Get free key from https://console.groq.com/)
GROQ_API_KEY=
HUGGINGFACE_API_TOKEN=

# Computer Vision
FOOD_DETECTION_MODEL=nateraw/food
DIP_DEBUG_MODE=true
DIP_DEBUG_OUTPUT_DIR=dip_debug_output

# File Upload
MAX_UPLOAD_SIZE=10485760
UPLOAD_DIR=uploads
EOF
    echo "[OK] .env file created"
    echo ""
fi

echo "Starting GlutenGuard AI services..."
echo ""
echo "This will:"
echo "- Build Docker images (first time only - may take 5-10 minutes)"
echo "- Start backend (FastAPI) on port 8000"
echo "- Start frontend (React) on port 80"
echo ""

# Start services
docker-compose up -d --build

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to start services!"
    echo "Check the error messages above."
    exit 1
fi

echo ""
echo "========================================"
echo "  Services Started Successfully!"
echo "========================================"
echo ""
echo "Frontend:  http://localhost"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "To view logs:    docker-compose logs -f"
echo "To stop:         docker-compose down"
echo ""

# Open browser (if available)
if command -v xdg-open > /dev/null; then
    echo "Opening browser..."
    sleep 3
    xdg-open http://localhost
elif command -v open > /dev/null; then
    echo "Opening browser..."
    sleep 3
    open http://localhost
fi

