"""RAG Retrieval Service - Retrieves relevant context from knowledge base"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from models import Meal, Symptom
import json

class RetrievalService:
    """
    Retrieval-Augmented Generation (RAG) Service
    
    Retrieves relevant historical data from the knowledge base (SQLite) 
    to augment LLM prompts with user-specific context.
    
    This implements a lightweight RAG pattern:
    - Retrieve: Query relevant meals/symptoms based on semantic similarity
    - Augment: Format retrieved data as context for LLM
    - Generate: LLM uses augmented context to produce better responses
    """
    
    def __init__(self):
        """Initialize retrieval service"""
        self.max_retrieved_items = 10  # Limit context size
    
    def retrieve_relevant_meals(
        self, 
        db: Session, 
        user_id: int,
        query_keywords: Optional[List[str]] = None,
        gluten_risk_min: Optional[float] = None,
        days_back: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve meals relevant to a query from knowledge base
        
        This is the "Retrieval" part of RAG - searches historical meal data
        based on semantic relevance (keywords, gluten risk, recency)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.timestamp >= cutoff_date
        )
        
        # Semantic search: Filter by keywords in description or detected foods
        if query_keywords:
            keyword_filters = []
            for keyword in query_keywords:
                keyword_filters.append(Meal.description.ilike(f"%{keyword}%"))
            query = query.filter(or_(*keyword_filters))
        
        # Filter by gluten risk threshold
        if gluten_risk_min is not None:
            query = query.filter(Meal.gluten_risk_score >= gluten_risk_min)
        
        # Order by relevance (most recent + highest gluten risk)
        meals = query.order_by(
            Meal.gluten_risk_score.desc(),
            Meal.timestamp.desc()
        ).limit(limit).all()
        
        # Format as retrieval results
        results = []
        for meal in meals:
            foods = []
            if meal.detected_foods:
                try:
                    foods_data = json.loads(meal.detected_foods) if isinstance(meal.detected_foods, str) else meal.detected_foods
                    foods = [f.get('name', str(f)) if isinstance(f, dict) else str(f) for f in foods_data]
                except:
                    foods = []
            
            results.append({
                "id": meal.id,
                "description": meal.description,
                "foods": foods,
                "gluten_risk": meal.gluten_risk_score,
                "timestamp": meal.timestamp.isoformat(),
                "meal_type": meal.meal_type
            })
        
        return results
    
    def retrieve_relevant_symptoms(
        self,
        db: Session,
        user_id: int,
        query_keywords: Optional[List[str]] = None,
        symptom_types: Optional[List[str]] = None,
        severity_min: Optional[float] = None,
        days_back: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve symptoms relevant to a query from knowledge base
        
        Searches symptom history based on type, severity, and keywords
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = db.query(Symptom).filter(
            Symptom.user_id == user_id,
            Symptom.timestamp >= cutoff_date
        )
        
        # Filter by symptom types
        if symptom_types:
            query = query.filter(Symptom.symptom_type.in_(symptom_types))
        
        # Filter by keywords
        if query_keywords:
            keyword_filters = []
            for keyword in query_keywords:
                keyword_filters.append(Symptom.description.ilike(f"%{keyword}%"))
            query = query.filter(or_(*keyword_filters))
        
        # Filter by severity
        if severity_min is not None:
            query = query.filter(Symptom.severity >= severity_min)
        
        # Order by relevance (severity + recency)
        symptoms = query.order_by(
            Symptom.severity.desc(),
            Symptom.timestamp.desc()
        ).limit(limit).all()
        
        # Format as retrieval results
        results = []
        for symptom in symptoms:
            results.append({
                "id": symptom.id,
                "description": symptom.description,
                "symptom_type": symptom.symptom_type,
                "severity": symptom.severity,
                "timestamp": symptom.timestamp.isoformat(),
                "time_context": symptom.time_context
            })
        
        return results
    
    def retrieve_correlated_pairs(
        self,
        db: Session,
        user_id: int,
        time_window_hours: int = 6,
        days_back: int = 30,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve meal-symptom pairs that show temporal correlation
        
        Finds meals followed by symptoms within a time window
        This helps identify patterns for RAG context
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        meals = db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.timestamp >= cutoff_date,
            Meal.gluten_risk_score >= 70  # High gluten meals
        ).order_by(Meal.timestamp.desc()).limit(limit * 3).all()  # Get more to filter
        
        symptoms = db.query(Symptom).filter(
            Symptom.user_id == user_id,
            Symptom.timestamp >= cutoff_date
        ).all()
        
        # Find correlated pairs
        pairs = []
        for meal in meals:
            meal_time = meal.timestamp
            window_end = meal_time + timedelta(hours=time_window_hours)
            
            # Find symptoms within time window
            related_symptoms = [
                s for s in symptoms 
                if meal_time <= s.timestamp <= window_end
            ]
            
            if related_symptoms:
                # Sort by severity
                related_symptoms.sort(key=lambda s: s.severity, reverse=True)
                top_symptom = related_symptoms[0]
                
                pairs.append({
                    "meal": {
                        "id": meal.id,
                        "description": meal.description,
                        "gluten_risk": meal.gluten_risk_score,
                        "timestamp": meal.timestamp.isoformat()
                    },
                    "symptom": {
                        "id": top_symptom.id,
                        "description": top_symptom.description,
                        "symptom_type": top_symptom.symptom_type,
                        "severity": top_symptom.severity,
                        "timestamp": top_symptom.timestamp.isoformat()
                    },
                    "time_lag_hours": (top_symptom.timestamp - meal.timestamp).total_seconds() / 3600
                })
            
            if len(pairs) >= limit:
                break
        
        return pairs
    
    def format_retrieval_context(
        self,
        retrieved_meals: List[Dict[str, Any]],
        retrieved_symptoms: List[Dict[str, Any]],
        correlated_pairs: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Format retrieved data as context for LLM augmentation
        
        This is the "Augmentation" part of RAG - structures retrieved data
        into a prompt that the LLM can use to generate better responses
        """
        context_parts = []
        
        if retrieved_meals:
            context_parts.append(f"RETRIEVED MEALS (Recent High-Gluten):")
            for meal in retrieved_meals[:5]:  # Top 5
                foods_str = ", ".join(meal.get("foods", [])) if meal.get("foods") else meal["description"]
                context_parts.append(
                    f"• {foods_str} - Gluten Risk: {meal['gluten_risk']}/100 ({meal.get('meal_type', 'meal')})"
                )
        
        if retrieved_symptoms:
            context_parts.append(f"\nRETRIEVED SYMPTOMS (Recent Severe):")
            for symptom in retrieved_symptoms[:5]:  # Top 5
                context_parts.append(
                    f"• {symptom['symptom_type']}: {symptom['description']} (Severity: {symptom['severity']}/10)"
                )
        
        if correlated_pairs:
            context_parts.append(f"\nRETRIEVED CORRELATIONS (Meal → Symptom Patterns):")
            for pair in correlated_pairs[:3]:  # Top 3
                meal_desc = pair['meal']['description'][:50]
                symptom_desc = pair['symptom']['description'][:50]
                lag = pair['time_lag_hours']
                context_parts.append(
                    f"• {meal_desc} → {symptom_desc} ({lag:.1f}h later)"
                )
        
        context_str = "\n".join(context_parts)
        
        if not context_parts:
            context_str = "No relevant historical data retrieved from knowledge base."
        
        return context_str
    
    def get_retrieval_stats(
        self,
        retrieved_meals: List[Dict[str, Any]],
        retrieved_symptoms: List[Dict[str, Any]],
        correlated_pairs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, int]:
        """
        Get statistics about what was retrieved for UI display
        
        Shows users that RAG is working by displaying retrieval counts
        """
        return {
            "meals_retrieved": len(retrieved_meals),
            "symptoms_retrieved": len(retrieved_symptoms),
            "correlations_retrieved": len(correlated_pairs) if correlated_pairs else 0,
            "total_items_retrieved": len(retrieved_meals) + len(retrieved_symptoms) + (len(correlated_pairs) if correlated_pairs else 0)
        }

