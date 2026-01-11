"""Insights endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel

from database import get_db
from models import Meal, Symptom
from services.insights_service import InsightsService

router = APIRouter()
insights_service = InsightsService()

class InsightResponse(BaseModel):
    insights: List[str]

@router.get("/smart-insights", response_model=InsightResponse)
def get_smart_insights(
    user_id: int = Query(1, description="User ID"),
    days: int = Query(7, description="Days of data to analyze"),
    db: Session = Depends(get_db)
):
    """Get AI-generated smart insights"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get meals and symptoms
        meals = db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.timestamp >= cutoff_date
        ).all()
        
        symptoms = db.query(Symptom).filter(
            Symptom.user_id == user_id,
            Symptom.timestamp >= cutoff_date
        ).all()
        
        # Generate insights
        insights = insights_service.generate_insights(meals, symptoms, days)
        
        return InsightResponse(insights=insights)
        
    except Exception as e:
        import traceback
        print(f"❌ Insights error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

