"""Configuration management for GlutenGuard AI"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Find .env file location and load it explicitly into os.environ
backend_dir = Path(__file__).parent
root_dir = backend_dir.parent
env_path = backend_dir / ".env"
if not env_path.exists():
    env_path = root_dir / ".env"

# Explicitly load .env file into os.environ FIRST, before Pydantic Settings
if env_path.exists():
    # Try utf-8-sig first (handles BOM), then fallback to utf-8
    try:
        load_dotenv(dotenv_path=env_path, override=True, encoding='utf-8-sig')
    except:
        load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded .env from: {env_path}")
    
    # Verify it loaded - if not, manually read and set it
    test_key = os.getenv("GROQ_API_KEY")
    if test_key:
        # Clean the key thoroughly
        test_key = test_key.strip().strip('\ufeff').strip('\u200b').strip('\n').strip('\r')
        # Update os.environ with cleaned key
        if test_key != os.getenv("GROQ_API_KEY"):
            os.environ['GROQ_API_KEY'] = test_key
        
        if test_key and test_key.startswith('gsk_'):
            masked = test_key[:10] + "..." + test_key[-4:] if len(test_key) > 14 else "***"
            print(f"   ✅ GROQ_API_KEY loaded: {masked} (length: {len(test_key)})")
        else:
            print(f"   ⚠️ GROQ_API_KEY format issue - trying manual read...")
            test_key = None
    
    if not test_key or not test_key.startswith('gsk_'):
        # Manual fallback: read file directly with BOM handling
        try:
            with open(env_path, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    if 'GROQ_API_KEY' in line and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip().strip('\ufeff')
                        value = value.strip().strip('"').strip("'").strip('\n').strip('\r')
                        value = value.replace('\ufeff', '').replace('\u200b', '')
                        if key == 'GROQ_API_KEY' and value and value.startswith('gsk_'):
                            os.environ['GROQ_API_KEY'] = value
                            masked = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
                            print(f"   ✅ Manually loaded GROQ_API_KEY: {masked} (length: {len(value)})")
                            break
        except Exception as e:
            print(f"   ❌ Error manually reading .env: {e}")
else:
    load_dotenv(override=True)
    print(f"⚠️ .env file not found at {env_path}, trying default locations")

# Get absolute path to .env file for Pydantic (it will also use os.environ)
env_file_str = str(env_path.absolute()) if env_path.exists() else ".env"

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./glutenguard.db"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS - store as string, parse as property
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # HuggingFace
    HUGGINGFACE_API_TOKEN: str = ""
    
    # Groq AI (Free Vision LLM for accurate food detection)
    # Read from environment variable (loaded from .env above)  
    # Clean the key to remove any BOM or hidden characters
    _raw_key = os.getenv("GROQ_API_KEY", "")
    if _raw_key:
        _clean_key = _raw_key.strip().strip('\ufeff').strip('\u200b').strip('\n').strip('\r')
        # Remove any quotes if present
        _clean_key = _clean_key.strip('"').strip("'")
        GROQ_API_KEY: str = _clean_key
    else:
        GROQ_API_KEY: str = ""
    
    # Food Detection Model (fallback if Groq unavailable)
    FOOD_DETECTION_MODEL: str = "nateraw/food"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # Digital Image Processing (DIP) Debug Mode
    DIP_DEBUG_MODE: bool = True
    DIP_DEBUG_OUTPUT_DIR: str = "dip_debug_output"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    class Config:
        env_file = env_file_str if env_path.exists() else None
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
        # Pydantic will read from os.environ (which we loaded with dotenv)

settings = Settings()

# Debug: Print Groq API key status (masked for security)
# Clean and validate the key
env_key_raw = os.getenv("GROQ_API_KEY", "")
env_key = env_key_raw.strip().strip('\ufeff').strip('\u200b').strip('\n').strip('\r') if env_key_raw else ""
if env_key != env_key_raw:
    os.environ['GROQ_API_KEY'] = env_key  # Update with cleaned version

settings_key_raw = settings.GROQ_API_KEY or ""
settings_key = settings_key_raw.strip().strip('\ufeff').strip('\u200b').strip('\n').strip('\r') if settings_key_raw else ""
if settings_key != settings_key_raw:
    settings.GROQ_API_KEY = settings_key  # Update with cleaned version

# Use the cleaner key
final_key = env_key or settings_key

if final_key:
    masked = final_key[:10] + "..." + final_key[-4:] if len(final_key) > 14 else "***"
    print(f"✅ GROQ_API_KEY loaded: {masked} (length: {len(final_key)})")
    if final_key.startswith('gsk_'):
        print(f"   ✅ Key format valid (starts with 'gsk_')")
    else:
        print(f"   ⚠️ WARNING: Key format may be invalid (should start with 'gsk_')")
        print(f"   Actual start: '{final_key[:5]}...'")
    # Ensure both locations have the cleaned key
    if env_key != final_key:
        os.environ['GROQ_API_KEY'] = final_key
    if settings_key != final_key:
        settings.GROQ_API_KEY = final_key
else:
    print(f"⚠️ GROQ_API_KEY not found - AI features will not work")
    print(f"   Please check: {env_path}")

