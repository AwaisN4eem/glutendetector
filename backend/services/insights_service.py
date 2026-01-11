"""Insights Service for proactive AI-generated health insights with RAG"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
from groq import Groq
from config import settings
from models import Meal, Symptom
from services.analysis_service import AnalysisService
from services.retrieval_service import RetrievalService

class InsightsService:
    """Service for generating proactive health insights"""
    
    def __init__(self):
        """Initialize Insights service"""
        self.groq_client = None
        api_key = (settings.GROQ_API_KEY or "").strip().strip('\ufeff').strip('\u200b')
        if api_key and api_key.startswith('gsk_'):
            try:
                self.groq_client = Groq(api_key=api_key)
                print("✅ Groq API initialized for Insights")
            except Exception as e:
                print(f"⚠️ Could not initialize Groq for Insights: {e}")
                import traceback
                traceback.print_exc()
        else:
            if api_key:
                print(f"⚠️ GROQ_API_KEY format invalid (should start with 'gsk_'). Insights will not be available.")
            else:
                print("⚠️ GROQ_API_KEY is empty or not set. Insights will not be available.")
        
        self.analysis_service = AnalysisService()
        self.retrieval_service = RetrievalService()
    
    def generate_insights(self, meals: List[Meal], symptoms: List[Symptom], days: int = 7) -> List[str]:
        """
        Generate proactive insights using RAG (Retrieval-Augmented Generation)
        
        RAG Pattern:
        1. Retrieve: Query patterns from meals/symptoms (high-gluten foods, symptom clusters)
        2. Augment: Format patterns as context for LLM
        3. Generate: LLM creates actionable insights from retrieved patterns
        """
        """Generate proactive insights based on user's data patterns"""
        if not self.groq_client:
            return []
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            recent_meals = [m for m in meals if m.timestamp >= cutoff_date]
            recent_symptoms = [s for s in symptoms if s.timestamp >= cutoff_date]
            
            if len(recent_meals) < 3 or len(recent_symptoms) < 2:
                return []  # Not enough data for insights
            
            # Analyze patterns
            patterns = self._analyze_patterns(recent_meals, recent_symptoms)
            
            # Generate insights using LLM
            insights = self._generate_insights_with_llm(patterns, recent_meals, recent_symptoms)
            
            return insights[:3]  # Return top 3 insights
            
        except Exception as e:
            print(f"⚠️ Insights generation error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _analyze_patterns(self, meals: List[Meal], symptoms: List[Symptom]) -> Dict[str, Any]:
        """
        Analyze patterns in meals and symptoms (RAG RETRIEVAL step)
        
        This is the "Retrieval" phase of RAG - extract relevant patterns from knowledge base
        """
        patterns = {
            "high_gluten_foods": [],
            "symptom_clusters": {},
            "time_patterns": {},
            "correlation_indicators": []
        }
        
        # Find high-gluten foods eaten frequently
        food_gluten_map = {}
        for meal in meals:
            if meal.gluten_risk_score >= 70:
                if meal.detected_foods:
                    import json
                    foods = json.loads(meal.detected_foods) if isinstance(meal.detected_foods, str) else meal.detected_foods
                    for food in foods:
                        # Handle both string and dict formats
                        if isinstance(food, dict):
                            food_name = food.get('name', food.get('food', str(food)))
                        else:
                            food_name = str(food)
                        
                        if food_name:
                            if food_name not in food_gluten_map:
                                food_gluten_map[food_name] = {"count": 0, "avg_risk": 0, "total_risk": 0}
                            food_gluten_map[food_name]["count"] += 1
                            food_gluten_map[food_name]["total_risk"] += meal.gluten_risk_score
        
        for food_name, data in food_gluten_map.items():
            if data["count"] >= 2:  # Eaten at least twice
                data["avg_risk"] = data["total_risk"] / data["count"]
                patterns["high_gluten_foods"].append({
                    "food": food_name,
                    "count": data["count"],
                    "avg_risk": data["avg_risk"]
                })
        
        patterns["high_gluten_foods"].sort(key=lambda x: x["count"], reverse=True)
        
        # Find symptom clusters
        symptom_counts = defaultdict(int)
        for symptom in symptoms:
            symptom_type = symptom.symptom_type or "unknown"
            symptom_counts[symptom_type] += 1
        
        patterns["symptom_clusters"] = dict(symptom_counts)
        
        # Time patterns (weekday vs weekend)
        weekday_symptoms = 0
        weekend_symptoms = 0
        for symptom in symptoms:
            weekday = symptom.timestamp.weekday() < 5  # 0-4 = Mon-Fri
            if weekday:
                weekday_symptoms += 1
            else:
                weekend_symptoms += 1
        
        if weekday_symptoms + weekend_symptoms > 0:
            weekday_pct = (weekday_symptoms / (weekday_symptoms + weekend_symptoms)) * 100
            patterns["time_patterns"]["weekday_vs_weekend"] = {
                "weekday_pct": weekday_pct,
                "weekday_count": weekday_symptoms,
                "weekend_count": weekend_symptoms
            }
        
        # Correlation indicators
        if len(meals) >= 5 and len(symptoms) >= 5:
            try:
                correlation_analysis = self.analysis_service.calculate_correlation(meals, symptoms)
                if correlation_analysis.correlation_score >= 60:
                    patterns["correlation_indicators"].append({
                        "correlation": correlation_analysis.correlation_score,
                        "significant": correlation_analysis.significant
                    })
            except:
                pass
        
        return patterns
    
    def _generate_insights_with_llm(self, patterns: Dict[str, Any], meals: List[Meal], symptoms: List[Symptom]) -> List[str]:
        """
        Use LLM to generate natural language insights (RAG GENERATION step)
        
        This is the "Generation" phase of RAG - LLM uses retrieved patterns to generate insights
        """
        try:
            # Build pattern summary
            pattern_summary = f"""Data Patterns Detected:

1. High-Gluten Foods Frequently Eaten:
{chr(10).join([f"   - {p['food']}: eaten {p['count']} times, avg risk {p['avg_risk']:.0f}/100" for p in patterns['high_gluten_foods'][:5]]) if patterns['high_gluten_foods'] else "   - None detected"}

2. Common Symptoms:
{chr(10).join([f"   - {symptom}: {count} times" for symptom, count in list(patterns['symptom_clusters'].items())[:5]]) if patterns['symptom_clusters'] else "   - None detected"}

3. Time Patterns:
{chr(10).join([f"   - {key}: {value}" for key, value in patterns['time_patterns'].items()]) if patterns['time_patterns'] else "   - None detected"}

4. Correlation Indicators:
{chr(10).join([f"   - Correlation: {ind['correlation']:.1f}% (significant: {ind['significant']})" for ind in patterns['correlation_indicators']]) if patterns['correlation_indicators'] else "   - Not enough data"}

Total meals analyzed: {len(meals)}
Total symptoms analyzed: {len(symptoms)}"""
            
            prompt = f"""Analyze this health tracking data and generate 3 actionable, empathetic insights.

{pattern_summary}

Requirements:
- Each insight should be 1-2 sentences
- Be specific and reference actual data (e.g., "You've had bloating 3 times this week after eating bread products")
- Provide actionable advice (e.g., "Try avoiding gluten for 3 days and see if symptoms improve")
- Use empathetic, supportive tone
- Focus on patterns that could help the user
- Format as a simple list, one insight per line
- No numbering or bullets, just plain text lines

Example format:
We noticed you had bloating 3 times this week after eating bread products - consider trying gluten-free alternatives.
Your symptoms are 60% worse on weekdays vs weekends - could be stress-related or meal timing?
Try avoiding high-gluten foods like pizza and samosas for 3 days and track if symptoms improve.

Generate exactly 3 insights:"""
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a health insights generator. Create actionable, empathetic health insights based on data patterns."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse insights (split by newlines, filter empty)
            insights = [line.strip() for line in content.split('\n') if line.strip()]
            
            # Clean up (remove numbering, bullets, etc.)
            cleaned_insights = []
            for insight in insights:
                # Remove leading numbers, bullets, dashes
                insight = insight.lstrip('0123456789.-•* ').strip()
                if insight and len(insight) > 20:  # Minimum length
                    cleaned_insights.append(insight)
            
            return cleaned_insights[:3]  # Return max 3
            
        except Exception as e:
            print(f"⚠️ LLM insights generation error: {e}")
            return []

