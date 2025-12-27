"""Database configuration and session management"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency for getting database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    
    # Add detailed_description column if it doesn't exist (for existing databases)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(meals)"))
            columns = [row[1] for row in result]
            if 'detailed_description' not in columns:
                conn.execute(text("ALTER TABLE meals ADD COLUMN detailed_description TEXT"))
                conn.commit()
                print("✅ Added detailed_description column to meals table")
    except Exception as e:
        print(f"⚠️ Could not add detailed_description column: {e}")

