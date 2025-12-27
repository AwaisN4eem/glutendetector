"""Symptom logging endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Symptom
from schemas import SymptomCreate, SymptomResponse
from services.nlp_service import NLPService

router = APIRouter()
nlp_service = NLPService()

@router.post("/", response_model=SymptomResponse, status_code=201)
def create_symptom(
    symptom_data: SymptomCreate,
    user_id: int = Query(1, description="User ID"),
    db: Session = Depends(get_db)
):
    """Log a new symptom"""
    
    # Extract symptom information using NLP
    nlp_result = nlp_service.analyze_symptom(symptom_data.description)
    
    # Use provided severity or extracted severity
    severity = symptom_data.severity if symptom_data.severity is not None else nlp_result["severity"]
    
    # Create symptom record
    db_symptom = Symptom(
        user_id=user_id,
        description=symptom_data.description,
        severity=severity,
        timestamp=symptom_data.timestamp or datetime.utcnow(),
        input_method=symptom_data.input_method,
        raw_text=symptom_data.description,
        symptom_type=nlp_result["symptom_type"],
        extracted_symptoms=nlp_result["extracted_symptoms"],
        sentiment_score=nlp_result["sentiment_score"],
        time_context=nlp_result["time_context"]
    )
    
    db.add(db_symptom)
    db.commit()
    db.refresh(db_symptom)
    
    return db_symptom

@router.get("/", response_model=List[SymptomResponse])
def get_symptoms(
    user_id: int = Query(1, description="User ID"),
    limit: int = Query(50, le=100),
    skip: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get user's symptom history"""
    query = db.query(Symptom).filter(Symptom.user_id == user_id)
    
    if start_date:
        query = query.filter(Symptom.timestamp >= start_date)
    if end_date:
        query = query.filter(Symptom.timestamp <= end_date)
    
    symptoms = query.order_by(Symptom.timestamp.desc()).offset(skip).limit(limit).all()
    return symptoms

@router.get("/{symptom_id}", response_model=SymptomResponse)
def get_symptom(symptom_id: int, db: Session = Depends(get_db)):
    """Get a specific symptom"""
    symptom = db.query(Symptom).filter(Symptom.id == symptom_id).first()
    if not symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")
    return symptom

@router.delete("/{symptom_id}", status_code=204)
def delete_symptom(symptom_id: int, db: Session = Depends(get_db)):
    """Delete a symptom"""
    symptom = db.query(Symptom).filter(Symptom.id == symptom_id).first()
    if not symptom:
        raise HTTPException(status_code=404, detail="Symptom not found")
    
    db.delete(symptom)
    db.commit()
    return None

