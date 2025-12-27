"""SQLAlchemy database models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    meals = relationship("Meal", back_populates="user", cascade="all, delete-orphan")
    symptoms = relationship("Symptom", back_populates="user", cascade="all, delete-orphan")
    photos = relationship("FoodPhoto", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")

class Meal(Base):
    """Meal logging model"""
    __tablename__ = "meals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Meal details
    meal_type = Column(String)  # breakfast, lunch, dinner, snack
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Gluten analysis
    gluten_risk_score = Column(Float, default=0.0)  # 0-100
    detected_foods = Column(JSON)  # List of detected food items
    contains_gluten = Column(Boolean, default=False)
    gluten_sources = Column(JSON)  # List of specific gluten-containing items
    
    # Metadata
    input_method = Column(String)  # text, voice, photo
    raw_text = Column(Text)  # Original input
    detailed_description = Column(Text)  # Groq-generated detailed description for timeline
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="meals")
    photos = relationship("FoodPhoto", back_populates="meal")

class Symptom(Base):
    """Symptom logging model"""
    __tablename__ = "symptoms"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Symptom details
    symptom_type = Column(String, index=True)  # bloating, pain, fatigue, etc.
    description = Column(Text, nullable=False)
    severity = Column(Float, nullable=False)  # 0-10 scale
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # NLP extracted data
    extracted_symptoms = Column(JSON)  # List of medical entities
    sentiment_score = Column(Float)  # -1 to 1
    time_context = Column(String)  # "after lunch", "3 hours after eating"
    
    # Metadata
    input_method = Column(String)  # text, voice, emoji
    raw_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="symptoms")

class FoodPhoto(Base):
    """Food photo model"""
    __tablename__ = "food_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=True)
    
    # File details
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_size = Column(Integer)
    
    # Detection results
    detected_foods = Column(JSON)  # [{name, confidence, gluten_risk}]
    primary_food = Column(String)  # Main detected food
    gluten_risk_score = Column(Float, default=0.0)  # 0-100
    processing_time = Column(Float)  # seconds
    
    # Metadata
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="photos")
    meal = relationship("Meal", back_populates="photos")

class Report(Base):
    """Analysis report model"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Report period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Analysis results
    correlation_score = Column(Float)  # 0-100%
    confidence_level = Column(Float)  # Statistical confidence
    gluten_intolerance_detected = Column(Boolean)
    
    # Detailed findings
    pattern_analysis = Column(JSON)  # Time-lag patterns, dose-response, etc.
    symptom_summary = Column(JSON)  # Grouped symptoms
    meal_summary = Column(JSON)  # Gluten exposure summary
    recommendations = Column(Text)
    
    # Statistics
    total_meals_logged = Column(Integer)
    total_symptoms_logged = Column(Integer)
    gluten_exposure_days = Column(Integer)
    symptom_free_days = Column(Integer)
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    report_type = Column(String)  # weekly, final
    
    # Relationships
    user = relationship("User", back_populates="reports")

class GlutenDatabase(Base):
    """Gluten risk database for foods"""
    __tablename__ = "gluten_database"
    
    id = Column(Integer, primary_key=True, index=True)
    food_name = Column(String, unique=True, index=True, nullable=False)
    gluten_risk = Column(Integer, nullable=False)  # 0-100
    category = Column(String)  # grain, sauce, processed, safe, etc.
    description = Column(Text)
    hidden_source = Column(Boolean, default=False)
    aliases = Column(JSON)  # Alternative names

