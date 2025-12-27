"""Analysis service for pattern detection and correlation"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from scipy import stats
from models import Meal, Symptom
from schemas import CorrelationAnalysis, DashboardData, TimelineEntry

class AnalysisService:
    """Service for analyzing correlations and patterns"""
    
    def __init__(self):
        """Initialize analysis service"""
        # Time lag windows to check (in hours)
        self.time_lag_windows = [1, 2, 3, 4, 6, 8, 12, 24, 48]
    
    def calculate_correlation(self, meals: List[Meal], symptoms: List[Symptom]) -> CorrelationAnalysis:
        """
        Calculate correlation between gluten exposure and symptoms
        
        This is the core "AI intelligence" that determines if gluten is causing symptoms
        """
        
        # Create daily timeseries
        timeseries = self._create_daily_timeseries(meals, symptoms)
        
        # Calculate correlations at different time lags
        best_correlation, best_lag = self._find_best_time_lag_correlation(timeseries)
        
        # Dose-response analysis
        dose_response = self._analyze_dose_response(timeseries)
        
        # Statistical significance
        p_value = self._calculate_p_value(timeseries, best_correlation)
        significant = p_value < 0.05
        confidence_level = 1 - p_value if p_value < 1 else 0.0
        
        # Convert correlation to percentage (0-100)
        correlation_percentage = abs(best_correlation) * 100
        
        return CorrelationAnalysis(
            correlation_score=round(correlation_percentage, 1),
            confidence_level=round(confidence_level, 3),
            significant=significant,
            time_lag_hours=best_lag,
            dose_response=dose_response
        )
    
    def _create_daily_timeseries(self, meals: List[Meal], symptoms: List[Symptom]) -> Dict[str, Dict]:
        """
        Create daily timeseries of gluten exposure and symptom severity
        """
        timeseries = defaultdict(lambda: {"gluten_score": 0.0, "symptom_score": 0.0, "meal_count": 0, "symptom_count": 0})
        
        # Process meals
        for meal in meals:
            date_key = meal.timestamp.date().isoformat()
            timeseries[date_key]["gluten_score"] += meal.gluten_risk_score
            timeseries[date_key]["meal_count"] += 1
        
        # Process symptoms
        for symptom in symptoms:
            date_key = symptom.timestamp.date().isoformat()
            timeseries[date_key]["symptom_score"] += symptom.severity
            timeseries[date_key]["symptom_count"] += 1
        
        # Calculate averages
        for date_key in timeseries:
            if timeseries[date_key]["meal_count"] > 0:
                timeseries[date_key]["gluten_score"] /= timeseries[date_key]["meal_count"]
            if timeseries[date_key]["symptom_count"] > 0:
                timeseries[date_key]["symptom_score"] /= timeseries[date_key]["symptom_count"]
        
        return dict(timeseries)
    
    def _find_best_time_lag_correlation(self, timeseries: Dict[str, Dict]) -> tuple:
        """
        Find the time lag that produces the strongest correlation
        (gluten today → symptoms tomorrow/2 days later/etc.)
        """
        if len(timeseries) < 3:
            return 0.0, 0
        
        # Sort by date
        sorted_dates = sorted(timeseries.keys())
        
        # Try immediate correlation (same day)
        gluten_scores = [timeseries[d]["gluten_score"] for d in sorted_dates]
        symptom_scores = [timeseries[d]["symptom_score"] for d in sorted_dates]
        
        if len(gluten_scores) < 3:
            return 0.0, 0
        
        try:
            correlation, _ = stats.pearsonr(gluten_scores, symptom_scores)
            if np.isnan(correlation):
                correlation = 0.0
        except:
            correlation = 0.0
        
        best_correlation = correlation
        best_lag = 0
        
        # Try lagged correlations (gluten today → symptoms N days later)
        for lag_days in range(1, min(4, len(sorted_dates) - 1)):
            gluten_lagged = gluten_scores[:-lag_days]
            symptom_lagged = symptom_scores[lag_days:]
            
            if len(gluten_lagged) < 3:
                continue
            
            try:
                corr, _ = stats.pearsonr(gluten_lagged, symptom_lagged)
                if not np.isnan(corr) and abs(corr) > abs(best_correlation):
                    best_correlation = corr
                    best_lag = lag_days * 24  # Convert to hours
            except:
                continue
        
        return best_correlation, best_lag
    
    def _analyze_dose_response(self, timeseries: Dict[str, Dict]) -> bool:
        """
        Check if more gluten = worse symptoms (dose-response relationship)
        """
        if len(timeseries) < 5:
            return False
        
        # Categorize days by gluten exposure
        low_gluten_days = []
        high_gluten_days = []
        
        for data in timeseries.values():
            gluten = data["gluten_score"]
            symptoms = data["symptom_score"]
            
            if symptoms == 0:  # Skip symptom-free days for this analysis
                continue
            
            if gluten < 30:
                low_gluten_days.append(symptoms)
            elif gluten >= 70:
                high_gluten_days.append(symptoms)
        
        # Compare average symptoms
        if len(low_gluten_days) >= 2 and len(high_gluten_days) >= 2:
            avg_low = np.mean(low_gluten_days)
            avg_high = np.mean(high_gluten_days)
            
            return avg_high > avg_low * 1.2  # 20% worse on high gluten days
        
        return False
    
    def _calculate_p_value(self, timeseries: Dict[str, Dict], correlation: float) -> float:
        """
        Calculate statistical significance (p-value)
        """
        n = len(timeseries)
        
        if n < 3:
            return 1.0
        
        # Calculate t-statistic
        if abs(correlation) >= 1:
            return 0.001 if abs(correlation) == 1 else 1.0
        
        try:
            t_stat = correlation * np.sqrt((n - 2) / (1 - correlation**2))
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            return min(p_value, 1.0)
        except:
            return 1.0
    
    def generate_dashboard_data(self, meals: List[Meal], symptoms: List[Symptom]) -> DashboardData:
        """
        Generate summary data for dashboard
        """
        # Count unique days with gluten exposure
        gluten_days = set()
        symptom_days = set()
        
        gluten_scores = []
        symptom_severities = []
        
        for meal in meals:
            if meal.gluten_risk_score >= 70:  # High gluten
                gluten_days.add(meal.timestamp.date())
            gluten_scores.append(meal.gluten_risk_score)
        
        for symptom in symptoms:
            symptom_days.add(symptom.timestamp.date())
            symptom_severities.append(symptom.severity)
        
        # Calculate averages
        avg_gluten_risk = np.mean(gluten_scores) if gluten_scores else 0.0
        avg_symptom_severity = np.mean(symptom_severities) if symptom_severities else 0.0
        
        # Quick correlation preview
        correlation_preview = None
        if len(meals) >= 10 and len(symptoms) >= 10:
            timeseries = self._create_daily_timeseries(meals, symptoms)
            correlation, _ = self._find_best_time_lag_correlation(timeseries)
            correlation_preview = abs(correlation) * 100
        
        # Create recent timeline
        recent_timeline = self._create_recent_timeline(meals, symptoms, days=7)
        
        return DashboardData(
            total_meals=len(meals),
            total_symptoms=len(symptoms),
            gluten_exposure_days=len(gluten_days),
            symptom_days=len(symptom_days),
            avg_gluten_risk=round(avg_gluten_risk, 1),
            avg_symptom_severity=round(avg_symptom_severity, 1),
            correlation_preview=round(correlation_preview, 1) if correlation_preview else None,
            recent_timeline=recent_timeline
        )
    
    def _create_recent_timeline(self, meals: List[Meal], symptoms: List[Symptom], days: int) -> List[TimelineEntry]:
        """Create recent timeline entries"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        timeline = []
        
        for meal in meals:
            if meal.timestamp >= cutoff:
                timeline.append(TimelineEntry(
                    timestamp=meal.timestamp,
                    entry_type="meal",
                    description=meal.description[:100] if meal.description else "",
                    detailed_description=getattr(meal, 'detailed_description', None),
                    gluten_risk=meal.gluten_risk_score,
                    severity=None
                ))
        
        for symptom in symptoms:
            if symptom.timestamp >= cutoff:
                timeline.append(TimelineEntry(
                    timestamp=symptom.timestamp,
                    entry_type="symptom",
                    description=symptom.description[:100] if symptom.description else "",
                    detailed_description=None,  # Symptoms don't have detailed descriptions
                    gluten_risk=None,
                    severity=symptom.severity
                ))
        
        # Sort by timestamp (most recent first)
        timeline.sort(key=lambda x: x.timestamp, reverse=True)
        
        return timeline[:20]  # Return last 20 entries
    
    def generate_report(self, meals: List[Meal], symptoms: List[Symptom], 
                       start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report
        """
        # Calculate correlation
        correlation = self.calculate_correlation(meals, symptoms)
        
        # Determine if gluten intolerance detected
        gluten_intolerance = (
            correlation.correlation_score >= 60 and 
            correlation.significant
        )
        
        # Symptom summary
        symptom_summary = self._summarize_symptoms(symptoms)
        
        # Meal summary
        meal_summary = self._summarize_meals(meals)
        
        # Pattern analysis
        pattern_analysis = {
            "time_lag_detected": correlation.time_lag_hours,
            "dose_response_detected": correlation.dose_response,
            "correlation_strength": "strong" if correlation.correlation_score >= 70 else "moderate" if correlation.correlation_score >= 40 else "weak"
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(correlation, gluten_intolerance)
        
        # Calculate stats
        gluten_days = len(set(m.timestamp.date() for m in meals if m.gluten_risk_score >= 70))
        symptom_days = len(set(s.timestamp.date() for s in symptoms))
        total_days = (end_date - start_date).days
        symptom_free_days = total_days - symptom_days
        
        return {
            "correlation_score": correlation.correlation_score,
            "confidence_level": correlation.confidence_level,
            "gluten_intolerance_detected": gluten_intolerance,
            "pattern_analysis": pattern_analysis,
            "symptom_summary": symptom_summary,
            "meal_summary": meal_summary,
            "recommendations": recommendations,
            "total_meals_logged": len(meals),
            "total_symptoms_logged": len(symptoms),
            "gluten_exposure_days": gluten_days,
            "symptom_free_days": max(0, symptom_free_days)
        }
    
    def _summarize_symptoms(self, symptoms: List[Symptom]) -> Dict[str, Any]:
        """Summarize symptoms by type and severity"""
        symptom_types = defaultdict(list)
        
        for symptom in symptoms:
            symptom_types[symptom.symptom_type or "general"].append(symptom.severity)
        
        summary = {}
        for symptom_type, severities in symptom_types.items():
            summary[symptom_type] = {
                "count": len(severities),
                "avg_severity": round(np.mean(severities), 1),
                "max_severity": round(max(severities), 1)
            }
        
        return summary
    
    def _summarize_meals(self, meals: List[Meal]) -> Dict[str, Any]:
        """Summarize meal data"""
        high_gluten_meals = [m for m in meals if m.gluten_risk_score >= 70]
        low_gluten_meals = [m for m in meals if m.gluten_risk_score < 30]
        
        return {
            "total_meals": len(meals),
            "high_gluten_meals": len(high_gluten_meals),
            "low_gluten_meals": len(low_gluten_meals),
            "avg_gluten_risk": round(np.mean([m.gluten_risk_score for m in meals]), 1)
        }
    
    def _generate_recommendations(self, correlation: CorrelationAnalysis, 
                                 gluten_intolerance: bool) -> str:
        """Generate personalized recommendations"""
        if gluten_intolerance:
            rec = f"STRONG EVIDENCE of gluten intolerance detected ({correlation.correlation_score}% correlation). "
            rec += "Recommendation: Consult with a healthcare provider about gluten elimination. "
            
            if correlation.time_lag_hours:
                rec += f"Symptoms typically appear {correlation.time_lag_hours} hours after gluten consumption. "
            
            if correlation.dose_response:
                rec += "Higher gluten intake correlates with worse symptoms. "
            
            return rec
        
        elif correlation.correlation_score >= 40:
            return f"MODERATE correlation detected ({correlation.correlation_score}%). Continue tracking for 2-4 more weeks to gather more data. Consider reducing gluten intake to see if symptoms improve."
        
        else:
            return f"LOW correlation detected ({correlation.correlation_score}%). Gluten may not be the primary trigger for your symptoms. Consider tracking other potential triggers (dairy, sugar, stress, etc.)."

