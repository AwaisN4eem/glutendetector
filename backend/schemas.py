"""Pydantic schemas for request/response validation"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# ============= User Schemas =============
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= Meal Schemas =============
class MealBase(BaseModel):
    description: str
    meal_type: Optional[str] = None
    timestamp: Optional[datetime] = None

class MealCreate(MealBase):
    input_method: str = "text"

class MealUpdate(BaseModel):
    """Schema for updating a meal"""
    description: Optional[str] = None
    meal_type: Optional[str] = None
    timestamp: Optional[datetime] = None
    input_method: Optional[str] = None

class MealResponse(MealBase):
    id: int
    user_id: int
    gluten_risk_score: float
    detected_foods: Optional[List[Dict[str, Any]]] = None
    contains_gluten: bool
    gluten_sources: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= Symptom Schemas =============
class SymptomBase(BaseModel):
    description: str
    severity: Optional[float] = None
    timestamp: Optional[datetime] = None

class SymptomCreate(SymptomBase):
    input_method: str = "text"

class SymptomResponse(SymptomBase):
    id: int
    user_id: int
    symptom_type: Optional[str] = None
    extracted_symptoms: Optional[List[Dict[str, Any]]] = None
    sentiment_score: Optional[float] = None
    time_context: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= Food Photo Schemas =============
class FoodPhotoResponse(BaseModel):
    id: int
    filename: str
    detected_foods: List[Dict[str, Any]]
    primary_food: Optional[str] = None
    gluten_risk_score: float
    processing_time: float
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

# ============= Report Schemas =============
class ReportResponse(BaseModel):
    id: int
    start_date: datetime
    end_date: datetime
    correlation_score: Optional[float] = None
    confidence_level: Optional[float] = None
    gluten_intolerance_detected: Optional[bool] = None
    pattern_analysis: Optional[Dict[str, Any]] = None
    symptom_summary: Optional[Dict[str, Any]] = None
    meal_summary: Optional[Dict[str, Any]] = None
    recommendations: Optional[str] = None
    total_meals_logged: Optional[int] = None
    total_symptoms_logged: Optional[int] = None
    generated_at: datetime
    report_type: Optional[str] = None
    
    class Config:
        from_attributes = True

# ============= Analysis Schemas =============
class CorrelationAnalysis(BaseModel):
    """Correlation analysis results"""
    correlation_score: float = Field(..., ge=0, le=100, description="Correlation percentage")
    confidence_level: float = Field(..., ge=0, le=1, description="Statistical confidence")
    significant: bool = Field(..., description="Whether correlation is statistically significant")
    time_lag_hours: Optional[float] = Field(None, description="Average time between gluten and symptoms")
    dose_response: Optional[bool] = Field(None, description="Whether more gluten = worse symptoms")
    # Extended metadata for UI clarity
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_meals: int = 0
    total_symptoms: int = 0
    p_value: Optional[float] = None
    confidence_interval: Optional[List[float]] = None

class TimelineEntry(BaseModel):
    """Timeline entry for visualization"""
    id: Optional[int] = None  # Meal or symptom ID
    timestamp: datetime
    entry_type: str  # meal or symptom
    description: str
    detailed_description: Optional[str] = None  # Groq-generated detailed info
    gluten_risk: Optional[float] = None
    severity: Optional[float] = None

class DashboardData(BaseModel):
    """Dashboard summary data"""
    total_meals: int
    total_symptoms: int
    gluten_exposure_days: int
    symptom_days: int
    avg_gluten_risk: float
    avg_symptom_severity: float
    correlation_preview: Optional[float] = None
    recent_timeline: List[TimelineEntry]

