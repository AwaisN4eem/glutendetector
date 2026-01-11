"""Prediction endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from database import get_db
from models import Meal, Symptom
from services.prediction_service import PredictionService

router = APIRouter()
prediction_service = PredictionService()

class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    time_window_hours: Optional[int] = None
    reasoning: str

@router.get("/predict/{meal_id}", response_model=PredictionResponse)
def predict_symptoms(
    meal_id: int,
    user_id: int = Query(1, description="User ID"),
    db: Session = Depends(get_db)
):
    """Predict symptoms based on a meal"""
    try:
        # Get the meal
        meal = db.query(Meal).filter(Meal.id == meal_id, Meal.user_id == user_id).first()
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")
        
        # Get past meals and symptoms for context
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        past_meals = db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.timestamp >= cutoff_date,
            Meal.id != meal_id  # Exclude current meal
        ).all()
        
        past_symptoms = db.query(Symptom).filter(
            Symptom.user_id == user_id,
            Symptom.timestamp >= cutoff_date
        ).all()
        
        # Generate prediction
        prediction = prediction_service.predict_symptoms(meal, past_meals, past_symptoms)
        
        return PredictionResponse(
            prediction=prediction.get("prediction", "Unable to predict"),
            confidence=prediction.get("confidence", 0),
            time_window_hours=prediction.get("time_window_hours"),
            reasoning=prediction.get("reasoning", "Based on historical patterns")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Prediction error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate prediction: {str(e)}")

