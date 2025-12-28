# 🐳 Docker Quick Start Guide

Get GlutenGuard AI running in **3 simple steps** using Docker!

---

## ⚡ Super Quick Start (Windows)

```batch
# 1. Make sure Docker Desktop is running
# 2. Run the launcher script
docker-start.bat
```

That's it! The browser will open automatically at http://localhost

---

## ⚡ Super Quick Start (Linux/Mac)

```bash
# 1. Make sure Docker is running
# 2. Make script executable and run
chmod +x docker-start.sh
./docker-start.sh
```

That's it! Open http://localhost in your browser.

---

## 📋 Manual Start (All Platforms)

### Step 1: Start Docker
- **Windows/Mac:** Open Docker Desktop
- **Linux:** Ensure Docker service is running

### Step 2: Create Environment File (First Time Only)
```bash
# Create .env file with these contents:
cat > .env << 'EOF'
# Minimal configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# Optional: Add your Groq API key for better accuracy
# Get free key from: https://console.groq.com/
GROQ_API_KEY=
EOF
```

### Step 3: Start Services
```bash
# Build and start
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

### Step 4: Access Application
- **Frontend:** http://localhost
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 🛑 Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove all data (fresh start)
docker-compose down -v
```

---

## 🔧 Development Mode (Hot Reload)

For active development with live code reloading:

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Access at:
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```

---

## 🐛 Troubleshooting

### Services won't start?
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

### Port already in use?
Edit `docker-compose.yml` and change ports:
```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change 8001 to any free port
  frontend:
    ports:
      - "8080:80"    # Change 8080 to any free port
```

### Out of memory?
- Open Docker Desktop → Settings → Resources
- Increase Memory to 8GB
- Click "Apply & Restart"

---

## 📚 Full Documentation

See [README.Docker.md](README.Docker.md) for complete documentation including:
- Architecture details
- All Docker commands
- Production deployment
- Security best practices
- Advanced troubleshooting

---

## ✅ What's Included

✅ **Backend (FastAPI)**
- Python 3.11
- OpenCV, spaCy, PyTorch
- Auto-downloads AI models
- Port 8000

✅ **Frontend (React + Nginx)**
- Node.js 18
- React with Tailwind CSS
- Production-optimized build
- Port 80

✅ **Data Persistence**
- SQLite database
- User uploads
- Debug output
- Application logs

✅ **Networking**
- Internal network for services
- Automatic service discovery
- Health checks

---

## 🎯 First Test

1. Open http://localhost
2. Click "Upload Photo"
3. Upload any food photo
4. Watch AI detect food in <2 seconds! 🚀

---

## 📞 Need Help?

- Check [README.Docker.md](README.Docker.md) for detailed docs
- View logs: `docker-compose logs -f`
- Check status: `docker-compose ps`
- Restart: `docker-compose restart`

---

**Happy Dockerizing! 🐳**

