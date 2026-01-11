"""AI Coach endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from database import get_db
from models import Meal, Symptom
from services.ai_coach_service import AICoachService

router = APIRouter()
ai_coach_service = AICoachService()

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    retrieval_stats: dict = {}

@router.post("/chat", response_model=ChatResponse)
def ai_coach_chat(
    request: ChatRequest,
    user_id: int = Query(1, description="User ID"),
    days: int = Query(7, description="Days of data to use for context"),
    db: Session = Depends(get_db)
):
    """Chat with AI Health Coach"""
    try:
        # Get user's meals and symptoms
        cutoff_date = datetime.utcnow() - timedelta(days=30)  # Get last 30 days for context
        
        meals = db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.timestamp >= cutoff_date
        ).all()
        
        symptoms = db.query(Symptom).filter(
            Symptom.user_id == user_id,
            Symptom.timestamp >= cutoff_date
        ).all()
        
        # Generate response (with RAG-enhanced context retrieval)
        answer, retrieval_stats = ai_coach_service.chat(request.question, meals, symptoms, db=db, user_id=user_id)
        
        return ChatResponse(answer=answer, retrieval_stats=retrieval_stats)
        
    except Exception as e:
        import traceback
        print(f"❌ AI Coach chat error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")

