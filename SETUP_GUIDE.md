# 🚀 GlutenGuard AI - Complete Setup Guide (VSCode on Windows)

Step-by-step instructions to get the project running in **under 10 minutes** on **Windows using VSCode**.

---
on
## 📋 Prerequisites Check

Before starting, ensure you have:

• [ ] **Python 3.11** installed (⚠️ **IMPORTANT: Use Python 3.11, not newer versions!**)
  ```powershell
  python --version  # Should be 3.11.x
  # OR
  py -3.11 --versi  # Should be 3.11.x
  ``
  **Why Python 3.11?** Many Python packages (wheels) cannot be installed on Python 3.12+ or advanced versions. Python 3.11 has the best compatibility with all required dependencies.

• [ ] **Node.js 18+** installed
  ```powershell
  node --version  # Should be 18 or higher
  npm --version
  ```

• [ ] **Git** installed
  ```powershell
  git --version
  ```

• [ ] **VSCode** installed (recommended)
  - Download from: https://code.visualstudio.com/

• [ ] **4GB RAM** minimum available

---

## 🔧 Installation Steps

### Step 1: Open Project in VSCode

1. Open **VSCode**
2. Click **File → Open Folder**
3. Navigate to your project folder (e.g., `G:\broke`)
4. Click **Select Folder**

You should now see the project structure in VSCode's Explorer panel.

---

### Step 2: Open Integrated Terminal in VSCode

1. In VSCode, press **`Ctrl + ``** (backtick) OR
2. Go to **Terminal → New Terminal** OR
3. Click **Terminal** tab at the bottom

This opens PowerShell/Command Prompt integrated in VSCode.

---

### Step 3: Backend Setup

#### 3.1 Navigate to Backend Directory

In the VSCode terminal, type:
```powershell
cd backend
```

#### 3.2 Create Virtual Environment with Python 3.11

**⚠️ CRITICAL: Use Python 3.11 specifically!**

```powershell
# Option 1: If python command points to 3.11
python -m venv venv

# Option 2: If you have multiple Python versions (RECOMMENDED)
py -3.11 -m venv venv
```

**Why `py -3.11 -m venv venv`?**
- Python 3.12+ and advanced versions have compatibility issues with many wheel packages
- Some dependencies (like `scipy`, `scikit-learn`, `opencv-python`) may fail to install on newer Python versions
- Python 3.11 has proven compatibility with all required packages
- Using `py -3.11` ensures you're using the correct Python version

**Expected output:**
```
(venv) PS G:\broke\backend>
```

If you see `(venv)` in your prompt, the virtual environment is active! ✅

#### 3.3 Activate Virtual Environment (if not already active)

If you don't see `(venv)` in your prompt:

```powershell
.\venv\Scripts\Activate.ps1
```

**If you get an execution policy error:**
```powershell
# Run this once (as Administrator):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activating again:
.\venv\Scripts\Activate.ps1
```

#### 3.4 Verify Python Version in Virtual Environment

```powershell
python --version
# Should show: Python 3.11.x
```

#### 3.5 Install Python Dependencies

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

This will take **3-5 minutes**. It installs:
• FastAPI (web framework)
• spaCy (NLP)
• Transformers (AI models)
• OpenCV (computer vision)
• PyTorch (deep learning)
• Matplotlib (visualization)
• And more...

**If you encounter errors:**
- Make sure you're using Python 3.11 (check with `python --version`)
- If packages fail to install, try: `pip install --upgrade pip setuptools wheel`
- Then retry: `pip install -r requirements.txt`

#### 3.6 Download NLP Model

```powershell
 python -m spacy download en_core_web_sm --direct
```

This downloads the English language model for spaCy (~50MB).

#### 3.7 Generate Sample Data (Optional but Recommended)

```powershell
python generate_sample_data.py 42
```

This creates:
• Demo user: `demo@glutenguard.ai` / `demo123`
• 42 days of realistic meal and symptom data
• Clear correlation pattern for demo

#### 3.8 Start Backend Server

```powershell
python run.py
```

You should see:
```
🌾 GlutenGuard AI - Starting Server
📍 Host: 0.0.0.0:8000
📚 API Docs: http://localhost:8000/docs
```

**Keep this terminal open!** The server is now running.

**Test it:** Open http://localhost:8000 in your browser. You should see:
```json
{
  "message": "Welcome to GlutenGuard AI",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

### Step 4: Frontend Setup

Open a **NEW terminal** in VSCode (keep backend running):
- Press **`Ctrl + Shift + ``** (new terminal) OR
- Click **+** button next to terminal tab OR
- Go to **Terminal → New Terminal**

#### 4.1 Navigate to Frontend

```powershell
cd frontend
# If you were in backend, use:
cd ..\frontend
```

#### 4.2 Install Node Dependencies

```powershell
npm install
```

This will take **1-2 minutes**.

#### 4.3 Start Frontend Server

```powershell
npm run dev
```

You should see:
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Keep this terminal open too!**

---

## ✅ Verify Installation

### 1. Check Backend Health

Open: http://localhost:8000/health

Should return:
```json
{"status": "healthy"}
```

### 2. Check API Documentation

Open: http://localhost:8000/docs

You should see interactive Swagger docs.

### 3. Check Frontend

Open: http://localhost:5173

You should see the GlutenGuard AI dashboard!

---

## 🎯 First Test Run

### Test 1: Upload Photo (⭐ Star Feature)

1. Go to http://localhost:5173
2. Click **"Upload Photo"** in navigation
3. Upload ANY food photo
4. Wait 1-2 seconds
5. You should see:
   • Detected foods
   • Gluten risk score (0-100)
   • Automatic meal logging
   • **DIP processing images** (if debug mode enabled):
     - Color models, enhancement, filtering
     - Edge detection, segmentation, morphology
     - Feature extraction (HOG, LBP, Moments)
     - **SIFT keypoints** (NEW)
     - **Corner detection** (Harris, Shi-Tomasi) (NEW)
     - **JPEG compression analysis** (NEW)

### Test 2: Log Symptom

1. Click **"Log Symptom"**
2. Type: "Terrible bloating 3 hours after lunch"
3. Set severity: 8/10
4. Click "Log Symptom"
5. You should see AI analysis:
   • Symptom type: Bloating
   • Time context: "3 hours after eating"
   • Sentiment analysis

### Test 3: View Dashboard

1. Click **"Dashboard"**
2. You should see:
   • Total meals/symptoms
   • Average gluten risk
   • Recent timeline
   • Correlation preview (if enough data)

### Test 4: Generate Report

1. Click **"Reports"**
2. Click "Generate Report"
3. You should see:
   • Correlation score (%)
   • Statistical significance
   • Time-lag analysis
   • Recommendations

### Test 5: Generate DIP Report Artifacts (For Academic Project)

1. In VSCode terminal (backend directory):
   ```powershell
   cd backend
   python generate_dip_report.py
   ```
2. This generates:
   • Confusion Matrix
   • Accuracy Tables
   • Runtime Graphs (including SIFT, Corner Detection, Compression methods)
   • Processing Pipeline Diagram (with all DIP steps: SIFT, Harris/Shi-Tomasi corners, JPEG compression)
3. Check `dip_report_artifacts/` folder for all generated files
4. Check `dip_debug_output/[session_id]/` for individual DIP processing images:
   • SIFT keypoints visualization
   • Harris and Shi-Tomasi corner detection
   • JPEG compression quality comparison

---

## 🐛 Troubleshooting

### Backend Won't Start

**Error: "ModuleNotFoundError"**
```powershell
# Make sure you're in virtual environment
.\venv\Scripts\Activate.ps1

# Verify Python version
python --version  # Should be 3.11.x

# Reinstall dependencies
pip install -r requirements.txt
```

**Error: "Python version not 3.11"**
```powershell
# Delete existing venv
Remove-Item -Recurse -Force venv

# Create new venv with Python 3.11
py -3.11 -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Verify version
python --version  # Should be 3.11.x

# Reinstall dependencies
pip install -r requirements.txt
```

**Error: "spacy model not found"**
```powershell
python -m spacy download en_core_web_sm
```

**Error: "Wheels cannot be installed" or "No matching distribution"**
```powershell
# This means you're using wrong Python version!
# Check version:
python --version

# If not 3.11.x, recreate venv:
Remove-Item -Recurse -Force venv
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

**Port 8000 already in use**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with actual PID)
taskkill /PID <PID> /F

# OR change port in backend/config.py or .env file:
# API_PORT=8001
```

**Error: "Execution Policy" when activating venv**
```powershell
# Run as Administrator:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate:
.\venv\Scripts\Activate.ps1
```

### Frontend Won't Start

**Error: "Cannot find module"**
```powershell
# Delete and reinstall
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

**Port 5173 already in use**
```powershell
# Kill existing process or change port in vite.config.js
```

### Photo Upload Not Working

**Error: "Upload failed"**
• Check backend is running (http://localhost:8000/health)
• Check file size (<10MB)
• Check file format (JPG, PNG, WEBP only)
• Check `uploads/` directory exists in backend folder

**Error: "Model not found"**
• HuggingFace models download on first use
• May take 30-60 seconds for first photo
• Requires internet connection
• Check logs in backend terminal

**DIP images not generating**
• Check `DIP_DEBUG_MODE=True` in `.env` file (or it's enabled by default)
• Check `dip_debug_output/` folder is created
• Check backend terminal for DIP processing messages

### Database Issues

**Error: "Database locked"**
```powershell
# Delete and regenerate
Remove-Item backend\glutenguard.db
cd backend
python generate_sample_data.py
```

---

## 🚀 Performance Optimization

### Speed Up Model Loading

First photo upload may be slow (model download). Subsequent uploads are fast.

To pre-download models:
```powershell
cd backend
python
# In Python shell:
>>> from transformers import AutoModelForImageClassification
>>> AutoModelForImageClassification.from_pretrained("nateraw/food")
>>> exit()
```

### Reduce Memory Usage

If system is slow:
• Close other applications
• Reduce sample data: `python generate_sample_data.py 14` (2 weeks instead of 6)
• Use production build: `npm run build` in frontend

---

## 📊 Development Workflow in VSCode

### Typical Development Session

**Terminal 1 (Backend):**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python run.py
```

**Terminal 2 (Frontend):**
```powershell
cd frontend
npm run dev
```

**Terminal 3 (Testing/Commands):**
```powershell
# Make API calls, test features, generate reports, etc.
cd backend
python generate_dip_report.py
```

### VSCode Tips

• **Split Terminal**: Right-click terminal tab → Split Terminal
• **Multiple Terminals**: Click **+** button to add more terminals
• **Terminal Selection**: Use dropdown to switch between PowerShell/CMD
• **Auto-save**: VSCode auto-saves files
• **Auto-reload**: Backend and frontend auto-reload on file changes

### Making Changes

• **Backend changes:** Server auto-reloads (debug mode)
• **Frontend changes:** Vite auto-reloads
• **Database changes:** Regenerate with `python generate_sample_data.py`

---

## 🎓 Next Steps

1. ✅ Verify all endpoints work: http://localhost:8000/docs
2. ✅ Upload multiple photos to test CV pipeline
3. ✅ Check `dip_debug_output/` for DIP processing images
4. ✅ Generate DIP report: `python generate_dip_report.py`
5. ✅ Log 10+ meals and symptoms
6. ✅ Generate your first correlation report
7. ✅ Review correlation analysis
8. ✅ Prepare demo presentation

---

## 📞 Still Having Issues?

• Check both servers are running (two terminals in VSCode)
• Check browser console for errors (F12)
• Check backend terminal for errors
• Verify ports 8000 and 5173 are available
• **Verify Python version is 3.11**: `python --version`
• Try restarting both servers
• If wheels installation fails, recreate venv with `py -3.11 -m venv venv`

---

## ⚠️ Important Notes for Windows/VSCode

### Python Version Requirement

**Always use Python 3.11 for this project!**

```powershell
# Correct way to create venv:
py -3.11 -m venv venv

# NOT:
python -m venv venv  # (if python points to 3.12+)
```

**Why?**
- Python 3.12+ has breaking changes
- Many wheel packages don't support newer Python versions yet
- `scipy`, `scikit-learn`, `opencv-python` may fail on 3.12+
- Python 3.11 is the sweet spot for compatibility

### Virtual Environment Activation

In VSCode terminal, always activate venv:
```powershell
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` in your prompt.

### Path Issues

If commands don't work:
• Use full paths: `.\venv\Scripts\python.exe` instead of `python`
• Or activate venv first: `.\venv\Scripts\Activate.ps1`

---

## ✨ You're Ready!

Both servers running? ✅  
Dashboard loads? ✅  
Photo upload works? ✅  
DIP images generating? ✅  

**Congratulations! You're ready to build the future of health tech! 🚀**

Try uploading a food photo right now - you'll be amazed! 📸

Then run `python generate_dip_report.py` to see all academic report artifacts! 📊
