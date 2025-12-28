# 🐳 Docker Deployment Guide - GlutenGuard AI

Complete guide for running GlutenGuard AI using Docker and Docker Compose.

---

## 📋 Prerequisites

### Required Software
- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
  - Download: https://www.docker.com/products/docker-desktop/
  - Minimum version: Docker 20.10+, Docker Compose v2.0+
- **4GB RAM** minimum (8GB recommended)
- **10GB** free disk space

### Verify Installation
```bash
docker --version
# Expected output: Docker version 20.10+ or higher

docker-compose --version
# Expected output: Docker Compose version v2.0+ or higher
```

---

## 🚀 Quick Start (Production Mode)

### 1. Clone Repository
```bash
git clone <repo-url>
cd broke
```

### 2. Create Environment File
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Groq API key (optional but recommended)
# Get free API key from: https://console.groq.com/
```

### 3. Build and Start Services
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Access Application
- **Frontend:** http://localhost
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

### 5. Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes database)
docker-compose down -v
```

---

## 🔧 Development Mode (Hot Reload)

For active development with live code reloading:

### Start Development Environment
```bash
# Build and start dev services
docker-compose -f docker-compose.dev.yml up

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Rebuild after dependency changes
docker-compose -f docker-compose.dev.yml up --build
```

### Development URLs
- **Frontend (Vite):** http://localhost:5173
- **Backend (FastAPI):** http://localhost:8000

### Features
- ✅ Live code reloading (backend and frontend)
- ✅ Source code mounted as volumes
- ✅ Faster iteration cycle
- ✅ Debug-friendly logging

### Stop Development Environment
```bash
docker-compose -f docker-compose.dev.yml down
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                    DOCKER HOST                  │
│                                                 │
│  ┌───────────────┐         ┌───────────────┐  │
│  │   Frontend    │         │   Backend     │  │
│  │  (Nginx:80)   │─────────│  (FastAPI)    │  │
│  │  React App    │   API   │   :8000       │  │
│  └───────┬───────┘         └───────┬───────┘  │
│          │                         │          │
│          └─────────────────────────┘          │
│               glutenguard-network             │
│                                                 │
│  Volumes:                                      │
│  • glutenguard.db (SQLite)                    │
│  • uploads/ (Photos)                          │
│  • dip_debug_output/ (CV debug)               │
│  • logs/ (Application logs)                   │
└─────────────────────────────────────────────────┘
```

---

## 📦 Services Description

### Backend Service
- **Image:** Python 3.11 slim
- **Port:** 8000
- **Volumes:**
  - `./backend/glutenguard.db` - SQLite database (persisted)
  - `./backend/uploads` - User uploaded photos (persisted)
  - `./backend/dip_debug_output` - CV debug images (persisted)
  - `./backend/logs` - Application logs (persisted)
- **Dependencies:**
  - FastAPI, OpenCV, spaCy, PyTorch, Transformers
  - Auto-downloads spaCy model on build
  - Installs system libraries for CV processing

### Frontend Service
- **Image:** Node 18 + Nginx alpine
- **Port:** 80 (production) or 5173 (dev)
- **Features:**
  - Multi-stage build (smaller image)
  - Nginx for production serving
  - Proxies API/uploads to backend
  - React Router SPA support

---

## 🔐 Environment Variables

### Required Variables (`.env` file)

```bash
# API Keys (optional but recommended)
GROQ_API_KEY=your_groq_api_key_here

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=change-this-to-random-secure-key
```

### Optional Variables

```bash
# Debug Mode
DEBUG=true
DIP_DEBUG_MODE=true

# Database
DATABASE_URL=sqlite:///./glutenguard.db

# CORS Origins
CORS_ORIGINS=http://localhost,http://localhost:80

# File Upload
MAX_UPLOAD_SIZE=10485760
```

### Getting API Keys

**Groq API Key (Free):**
1. Visit: https://console.groq.com/
2. Sign up for free account
3. Create API key
4. Add to `.env` file

**Without API Key:**
- System will use HuggingFace fallback model
- Still functional, slightly lower accuracy

---

## 📊 Docker Commands Reference

### Build Commands
```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend

# Build with no cache
docker-compose build --no-cache

# Pull latest images
docker-compose pull
```

### Run Commands
```bash
# Start services (detached)
docker-compose up -d

# Start with rebuild
docker-compose up --build

# Start specific service
docker-compose up backend

# Scale services (if needed)
docker-compose up --scale backend=2
```

### Stop Commands
```bash
# Stop services (keep containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### View Commands
```bash
# View running services
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100 backend

# Inspect service
docker-compose config
```

### Execute Commands
```bash
# Run command in backend
docker-compose exec backend python --version

# Access backend shell
docker-compose exec backend bash

# Access frontend shell
docker-compose exec frontend sh

# Run database migrations
docker-compose exec backend python -m alembic upgrade head

# Generate sample data
docker-compose exec backend python generate_sample_data.py 42
```

### Cleanup Commands
```bash
# Remove stopped containers
docker-compose rm -f

# Prune all unused images
docker image prune -a

# Prune all unused volumes
docker volume prune

# Full system cleanup
docker system prune -a --volumes
```

---

## 🐛 Troubleshooting

### Issue: Services won't start

**Check logs:**
```bash
docker-compose logs backend
docker-compose logs frontend
```

**Check container status:**
```bash
docker-compose ps
```

**Rebuild from scratch:**
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Backend can't connect to database

**Check volume permissions:**
```bash
# Linux/Mac
sudo chown -R $USER:$USER ./backend/glutenguard.db

# Windows
# Run Docker Desktop as Administrator
```

**Reset database:**
```bash
docker-compose down
rm backend/glutenguard.db
docker-compose up -d
```

### Issue: Frontend can't reach backend

**Check network:**
```bash
docker network ls
docker network inspect broke_glutenguard-network
```

**Check CORS settings:**
```bash
# Verify .env file
cat .env | grep CORS_ORIGINS

# Should include: http://localhost,http://localhost:80
```

### Issue: Port already in use

**Change ports in `docker-compose.yml`:**
```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change 8001 to any available port
  
  frontend:
    ports:
      - "8080:80"    # Change 8080 to any available port
```

### Issue: Out of memory

**Increase Docker memory:**
- Docker Desktop → Settings → Resources
- Increase Memory to 8GB
- Apply & Restart

### Issue: Slow build times

**Use build cache:**
```bash
docker-compose build --parallel
```

**Or use development mode:**
```bash
docker-compose -f docker-compose.dev.yml up
```

---

## 📈 Health Checks

### Backend Health
```bash
# HTTP request
curl http://localhost:8000/health

# Expected response: {"status":"healthy"}
```

### Frontend Health
```bash
# HTTP request
curl http://localhost/

# Should return HTML
```

### Docker Health Status
```bash
# View health status
docker-compose ps

# Expected: "healthy" in STATUS column
```

---

## 🔒 Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` to strong random string
- [ ] Set `DEBUG=false` in production
- [ ] Use HTTPS/SSL certificates (add reverse proxy)
- [ ] Restrict CORS origins to your domain
- [ ] Use secrets management (Docker Secrets, Vault)
- [ ] Enable firewall rules
- [ ] Regular backups of database
- [ ] Use Docker secrets instead of .env file

### Production docker-compose.yml example:
```yaml
version: '3.8'

services:
  backend:
    image: glutenguard-backend:latest
    restart: always
    environment:
      - DEBUG=false
    secrets:
      - groq_api_key
      - secret_key
    # ... rest of config

secrets:
  groq_api_key:
    external: true
  secret_key:
    external: true
```

---

## 📚 Additional Resources

- **Docker Documentation:** https://docs.docker.com/
- **Docker Compose Guide:** https://docs.docker.com/compose/
- **GlutenGuard AI Main README:** [../README.md](../README.md)
- **FastAPI Docker Guide:** https://fastapi.tiangolo.com/deployment/docker/

---

## 💡 Tips & Best Practices

1. **Use `.dockerignore`** - Already configured to exclude unnecessary files
2. **Layer Caching** - Dependencies are copied before code for faster rebuilds
3. **Multi-stage Builds** - Frontend uses multi-stage for smaller images
4. **Volume Mounts** - Data persists across container restarts
5. **Health Checks** - Automatic container health monitoring
6. **Networks** - Services communicate via internal network
7. **Development Mode** - Use `docker-compose.dev.yml` for active development

---

## 🎯 Next Steps

1. ✅ Start services: `docker-compose up -d`
2. ✅ Open browser: http://localhost
3. ✅ Upload food photo in "Upload Photo" page
4. ✅ Watch AI detect foods in <2 seconds!
5. ✅ Explore other features (voice input, symptom logging, reports)

---

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review [Troubleshooting](#-troubleshooting) section
3. Open GitHub issue with logs and error details

---

**Happy Dockerizing! 🐳🚀**

