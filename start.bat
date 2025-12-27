@echo off
REM Quick start script for GlutenGuard AI (Windows)

echo 🌾 GlutenGuard AI - Quick Start
echo ================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.10+
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 18+
    exit /b 1
)

echo ✅ Prerequisites check passed
echo.

REM Setup backend
echo 📦 Setting up backend...
cd backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -q -r requirements.txt

echo Downloading NLP model...
python -m spacy download en_core_web_sm

if not exist "glutenguard.db" (
    echo Generating sample data...
    python generate_sample_data.py 42
)

echo.
echo ✅ Backend setup complete!
echo.

REM Setup frontend
echo 📦 Setting up frontend...
cd ..\frontend

if not exist "node_modules" (
    echo Installing Node dependencies...
    call npm install
)

echo.
echo ✅ Frontend setup complete!
echo.

REM Instructions
echo 🚀 Ready to start!
echo.
echo Open TWO command prompts:
echo.
echo Command Prompt 1 (Backend):
echo   cd backend
echo   venv\Scripts\activate
echo   python run.py
echo.
echo Command Prompt 2 (Frontend):
echo   cd frontend
echo   npm run dev
echo.
echo Then open: http://localhost:5173
echo.
echo 🌟 Try uploading a food photo - it's amazing!
echo.
pause

