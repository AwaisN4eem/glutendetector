"""Explain endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from database import get_db
from models import Meal, Symptom
from services.explain_service import ExplainService

router = APIRouter()
explain_service = ExplainService()

class ExplainGlutenRiskRequest(BaseModel):
    food_name: str
    gluten_risk: float
    meal_description: Optional[str] = None

class ExplainCorrelationRequest(BaseModel):
    correlation_score: float
    p_value: Optional[float] = None
    total_meals: int = 0
    total_symptoms: int = 0

class ExplainResponse(BaseModel):
    explanation: str

@router.post("/gluten-risk", response_model=ExplainResponse)
def explain_gluten_risk(request: ExplainGlutenRiskRequest):
    """Explain why a food has a specific gluten risk score"""
    try:
        explanation = explain_service.explain_gluten_risk(
            request.food_name,
            request.gluten_risk,
            request.meal_description
        )
        return ExplainResponse(explanation=explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

@router.post("/correlation", response_model=ExplainResponse)
def explain_correlation(request: ExplainCorrelationRequest):
    """Explain what a correlation score means"""
    try:
        explanation = explain_service.explain_correlation(
            request.correlation_score,
            request.p_value,
            request.total_meals,
            request.total_symptoms
        )
        return ExplainResponse(explanation=explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

@router.get("/data-point/{entry_type}/{entry_id}", response_model=ExplainResponse)
def explain_data_point(
    entry_type: str,
    entry_id: int,
    user_id: int = Query(1, description="User ID"),
    db: Session = Depends(get_db)
):
    """Explain a specific data point (meal or symptom)"""
    try:
        meal = None
        symptom = None
        
        if entry_type == "meal":
            meal = db.query(Meal).filter(Meal.id == entry_id, Meal.user_id == user_id).first()
            if not meal:
                raise HTTPException(status_code=404, detail="Meal not found")
        elif entry_type == "symptom":
            symptom = db.query(Symptom).filter(Symptom.id == entry_id, Symptom.user_id == user_id).first()
            if not symptom:
                raise HTTPException(status_code=404, detail="Symptom not found")
        else:
            raise HTTPException(status_code=400, detail="Invalid entry type. Use 'meal' or 'symptom'")
        
        explanation = explain_service.explain_data_point(meal=meal, symptom=symptom)
        return ExplainResponse(explanation=explanation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

