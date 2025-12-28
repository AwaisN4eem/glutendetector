# GlutenGuard AI - Frontend

Modern React frontend for the GlutenGuard AI gluten intolerance detection system.

## Features

• **Dashboard:** Real-time stats and correlation preview
• **Photo Upload:** AI-powered food detection (⭐ Star Feature)
• **Meal/Symptom Logging:** Simple text-based input with AI analysis
• **Timeline:** Visual history of all meals and symptoms
• **Reports:** Comprehensive correlation analysis with statistical significance

## Tech Stack

• React 18
• Vite (dev server)
• Tailwind CSS (styling)
• Chart.js (visualizations)
• React Router (navigation)
• Axios (API calls)
• Lucide React (icons)

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

Frontend runs at: http://localhost:5173

### 3. Build for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── pages/           # Page components
│   │   ├── Dashboard.jsx
│   │   ├── UploadPhoto.jsx  (⭐ Star Feature)
│   │   ├── LogMeal.jsx
│   │   ├── LogSymptom.jsx
│   │   ├── Timeline.jsx
│   │   └── Reports.jsx
│   ├── components/      # Reusable components
│   │   └── Layout.jsx
│   ├── api/            # API client
│   │   └── client.js
│   ├── App.jsx         # Main app component
│   ├── main.jsx        # Entry point
│   └── index.css       # Global styles
├── public/
├── index.html
├── vite.config.js
├── tailwind.config.js
└── package.json
```

## Key Features

### 🌟 Photo Upload (Star Feature)
• Drag & drop food photo
• AI detects foods with 90%+ accuracy
• Automatic gluten risk calculation
• Auto-creates meal entry
• Processing: <2 seconds

### 📊 Dashboard
• Real-time statistics
• Correlation preview
• Recent activity timeline
• Visual progress charts

### 📝 Smart Logging
• NLP-powered meal analysis
• Symptom severity tracking
• Time context extraction
• Automatic gluten risk scoring

### 📈 Reports & Analysis
• Statistical correlation analysis
• Time-lag detection
• Dose-response patterns
• Confidence levels & p-values

## API Integration

All API calls go through `src/api/client.js`:

```javascript
import { api } from '../api/client'

// Upload photo
await api.uploadPhoto(file)

// Log meal
await api.createMeal({ description, meal_type })

// Log symptom
await api.createSymptom({ description, severity })

// Get correlation
await api.getCorrelation()
```

## Styling

Uses Tailwind CSS with custom primary color theme:

• Primary: Orange (#d97919)
• Accents: Blue, Red, Green for different data types
• Responsive design (mobile-first)
• Custom animations

## Environment Variables

Create `.env` file (optional):

```
VITE_API_URL=http://localhost:8000
```

If not set, defaults to `http://localhost:8000`

## Browser Support

• Chrome/Edge: Latest 2 versions
• Firefox: Latest 2 versions
• Safari: Latest 2 versions

## License

MIT License - Free for student projects

