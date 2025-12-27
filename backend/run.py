"""Simple startup script for development"""
import os
import sys

# Ensure we're in the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run the server
if __name__ == "__main__":
    import uvicorn
    from config import settings
    
    print("=" * 60)
    print("🌾 GlutenGuard AI - Starting Server")
    print("=" * 60)
    print(f"📍 Host: {settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API Docs: http://localhost:{settings.API_PORT}/docs")
    print(f"🔍 Debug Mode: {settings.DEBUG}")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

