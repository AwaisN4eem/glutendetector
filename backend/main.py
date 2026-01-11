"""Main FastAPI application"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from config import settings
from database import init_db, get_db
from routers import meals, symptoms, photos, analysis, users, ai_coach, insights, explain, prediction, food_search

# Initialize FastAPI app
app = FastAPI(
    title="GlutenGuard AI",
    description="AI-powered gluten intolerance detection system",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5175", "http://127.0.0.1:5175"],  # Ensure localhost is included
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Create upload directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Mount static files for uploaded photos
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(meals.router, prefix="/api/meals", tags=["meals"])
app.include_router(symptoms.router, prefix="/api/symptoms", tags=["symptoms"])
app.include_router(photos.router, prefix="/api/photos", tags=["photos"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(ai_coach.router, prefix="/api/ai-coach", tags=["ai-coach"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(explain.router, prefix="/api/explain", tags=["explain"])
app.include_router(prediction.router, prefix="/api/prediction", tags=["prediction"])
app.include_router(food_search.router, prefix="/api/food-search", tags=["food-search"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and resources on startup"""
    print("🚀 Starting GlutenGuard AI...")
    init_db()
    print("✅ Database initialized")
    
    # Initialize gluten database if empty
    from services.gluten_db_service import initialize_gluten_database
    db = next(get_db())
    initialize_gluten_database(db)
    print("✅ Gluten database initialized")
    
    # Initialize RAG vector store (FAISS index for semantic food search)
    try:
        from routers.food_search import rag_service
        rag_service.build_food_index(db)
        print("✅ RAG vector store initialized (FAISS + sentence-transformers)")
    except Exception as e:
        print(f"⚠️ RAG initialization failed: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to GlutenGuard AI",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

