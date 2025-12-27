"""Configuration management for GlutenGuard AI"""
import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./glutenguard.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS
    CORS_ORIGINS: List[str] = [origin.strip() for origin in os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:5173"
    ).split(",") if origin.strip()]
    
    # HuggingFace
    HUGGINGFACE_API_TOKEN: str = os.getenv("HUGGINGFACE_API_TOKEN", "")
    
    # Groq AI (Free Vision LLM for accurate food detection)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Food Detection Model (fallback if Groq unavailable)
    FOOD_DETECTION_MODEL: str = "nateraw/food"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # Digital Image Processing (DIP) Debug Mode
    DIP_DEBUG_MODE: bool = os.getenv("DIP_DEBUG_MODE", "True").lower() == "true"
    DIP_DEBUG_OUTPUT_DIR: str = os.getenv("DIP_DEBUG_OUTPUT_DIR", "dip_debug_output")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()

