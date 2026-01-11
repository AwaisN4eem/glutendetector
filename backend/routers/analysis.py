"""Analysis and reporting endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models import Meal, Symptom, Report
from schemas import CorrelationAnalysis, DashboardData, TimelineEntry, ReportResponse
from services.analysis_service import AnalysisService

router = APIRouter()
analysis_service = AnalysisService()

@router.get("/dashboard", response_model=DashboardData)
def get_dashboard(
    user_id: int = Query(1, description="User ID"),
    days: int = Query(14, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get dashboard summary data"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get meals and symptoms
        meals = db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.timestamp >= start_date
        ).all()
        
        symptoms = db.query(Symptom).filter(
            Symptom.user_id == user_id,
            Symptom.timestamp >= start_date
        ).all()
        
        # Calculate summary stats (handles empty lists gracefully)
        dashboard_data = analysis_service.generate_dashboard_data(meals, symptoms)
        
        return dashboard_data
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Dashboard error: {e}")
        print(error_trace)
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {str(e)}")

@router.get("/correlation", response_model=CorrelationAnalysis)
def get_correlation_analysis(
    user_id: int = Query(1, description="User ID"),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    db: Session = Depends(get_db)
):
    """Get correlation analysis between gluten and symptoms"""
    
    # Default to last 6 weeks if no dates provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(weeks=6)
    
    # Get meals and symptoms
    meals = db.query(Meal).filter(
        Meal.user_id == user_id,
        Meal.timestamp >= start_date,
        Meal.timestamp <= end_date
    ).all()
    
    symptoms = db.query(Symptom).filter(
        Symptom.user_id == user_id,
        Symptom.timestamp >= start_date,
        Symptom.timestamp <= end_date
    ).all()
    
    if len(meals) < 10 or len(symptoms) < 10:
        raise HTTPException(
            status_code=400,
            detail="Not enough data for correlation analysis (need at least 10 meals and 10 symptoms)"
        )
    
    # Perform correlation analysis
    correlation = analysis_service.calculate_correlation(
        meals,
        symptoms,
        start_date=start_date,
        end_date=end_date
    )
    
    return correlation

@router.get("/timeline", response_model=List[TimelineEntry])
def get_timeline(
    user_id: int = Query(1, description="User ID"),
    days: int = Query(7, description="Number of days"),
    db: Session = Depends(get_db)
):
    """Get combined timeline of meals and symptoms"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get meals and symptoms
    meals = db.query(Meal).filter(
        Meal.user_id == user_id,
        Meal.timestamp >= start_date
    ).all()
    
    symptoms = db.query(Symptom).filter(
        Symptom.user_id == user_id,
        Symptom.timestamp >= start_date
    ).all()
    
    # Create timeline
    timeline = []
    
    for meal in meals:
        timeline.append(TimelineEntry(
            id=meal.id,
            timestamp=meal.timestamp,
            entry_type="meal",
            description=meal.description,
            detailed_description=getattr(meal, 'detailed_description', None),  # Groq-generated details
            gluten_risk=meal.gluten_risk_score,
            severity=None
        ))
    
    for symptom in symptoms:
        timeline.append(TimelineEntry(
            id=symptom.id,
            timestamp=symptom.timestamp,
            entry_type="symptom",
            description=symptom.description,
            detailed_description=None,  # Symptoms don't have detailed descriptions
            gluten_risk=None,
            severity=symptom.severity
        ))
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x.timestamp, reverse=True)
    
    return timeline

@router.post("/generate-report", response_model=ReportResponse, status_code=201)
def generate_report(
    user_id: int = Query(1, description="User ID"),
    weeks: int = Query(6, description="Number of weeks to analyze"),
    db: Session = Depends(get_db)
):
    """Generate comprehensive analysis report"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(weeks=weeks)
    
    # Get all data
    meals = db.query(Meal).filter(
        Meal.user_id == user_id,
        Meal.timestamp >= start_date
    ).all()
    
    symptoms = db.query(Symptom).filter(
        Symptom.user_id == user_id,
        Symptom.timestamp >= start_date
    ).all()
    
    if len(meals) < 10 or len(symptoms) < 10:
        raise HTTPException(
            status_code=400,
            detail="Not enough data for report generation"
        )
    
    # Generate report
    report_data = analysis_service.generate_report(meals, symptoms, start_date, end_date)
    
    # Save report
    db_report = Report(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        report_type="final",
        **report_data
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return db_report

@router.get("/reports", response_model=List[ReportResponse])
def get_reports(
    user_id: int = Query(1, description="User ID"),
    db: Session = Depends(get_db)
):
    """Get all user reports"""
    try:
        reports = db.query(Report).filter(
            Report.user_id == user_id
        ).order_by(Report.generated_at.desc()).all()
        
        return reports or []  # Return empty list if no reports
    except Exception as e:
        import traceback
        print(f"❌ Reports error: {e}")
        print(traceback.format_exc())
        # Return empty list on error instead of crashing
        return []

