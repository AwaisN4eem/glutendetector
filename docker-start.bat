@echo off
REM Windows batch script to start GlutenGuard AI with Docker

echo ========================================
echo   GlutenGuard AI - Docker Launcher
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo Creating .env from template...
    echo.
    (
        echo # GlutenGuard AI - Environment Variables
        echo.
        echo # Backend Configuration
        echo API_HOST=0.0.0.0
        echo API_PORT=8000
        echo DEBUG=true
        echo DATABASE_URL=sqlite:///./glutenguard.db
        echo.
        echo # Security ^(CHANGE IN PRODUCTION!^)
        echo SECRET_KEY=dev-secret-key-change-in-production
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
        echo.
        echo # CORS Origins
        echo CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:80
        echo.
        echo # AI Services ^(Optional - Get free key from https://console.groq.com/^)
        echo GROQ_API_KEY=
        echo HUGGINGFACE_API_TOKEN=
        echo.
        echo # Computer Vision
        echo FOOD_DETECTION_MODEL=nateraw/food
        echo DIP_DEBUG_MODE=true
        echo DIP_DEBUG_OUTPUT_DIR=dip_debug_output
        echo.
        echo # File Upload
        echo MAX_UPLOAD_SIZE=10485760
        echo UPLOAD_DIR=uploads
    ) > .env
    echo [OK] .env file created
    echo.
)

echo Starting GlutenGuard AI services...
echo.
echo This will:
echo - Build Docker images (first time only - may take 5-10 minutes)
echo - Start backend (FastAPI) on port 8000
echo - Start frontend (React) on port 80
echo.

REM Start services
docker-compose up -d --build

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start services!
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Services Started Successfully!
echo ========================================
echo.
echo Frontend:  http://localhost
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo To view logs:    docker-compose logs -f
echo To stop:         docker-compose down
echo.
echo Opening browser...
timeout /t 3 >nul
start http://localhost

pause

