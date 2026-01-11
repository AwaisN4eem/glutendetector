"""Prediction Service for symptom forecasting"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from groq import Groq
from config import settings
from models import Meal, Symptom
from services.analysis_service import AnalysisService

class PredictionService:
    """Service for predicting symptoms based on meals"""
    
    def __init__(self):
        """Initialize Prediction service"""
        self.groq_client = None
        api_key = (settings.GROQ_API_KEY or "").strip().strip('\ufeff').strip('\u200b')
        if api_key and api_key.startswith('gsk_'):
            try:
                self.groq_client = Groq(api_key=api_key)
                print("✅ Groq API initialized for Prediction service")
            except Exception as e:
                print(f"⚠️ Could not initialize Groq for Prediction: {e}")
                import traceback
                traceback.print_exc()
        else:
            if api_key:
                print(f"⚠️ GROQ_API_KEY format invalid (should start with 'gsk_'). Prediction features will not be available.")
            else:
                print("⚠️ GROQ_API_KEY is empty or not set. Prediction features will not be available.")
        
        self.analysis_service = AnalysisService()
    
    def predict_symptoms(self, new_meal: Meal, past_meals: List[Meal], past_symptoms: List[Symptom]) -> Dict[str, Any]:
        """Predict likely symptoms based on a new meal and historical patterns"""
        if not self.groq_client or len(past_meals) < 5:
            return {
                "prediction": "Not enough data for prediction",
                "confidence": 0,
                "reasoning": "Need at least 5 past meals to make predictions"
            }
        
        try:
            # Find similar meals
            similar_meals = self._find_similar_meals(new_meal, past_meals)
            
            # Get outcomes for similar meals
            outcomes = self._get_past_outcomes(similar_meals, past_symptoms)
            
            # Get correlation data
            correlation = None
            if len(past_meals) >= 10 and len(past_symptoms) >= 10:
                try:
                    correlation_analysis = self.analysis_service.calculate_correlation(past_meals, past_symptoms)
                    correlation = correlation_analysis.correlation_score
                except:
                    pass
            
            # Generate prediction using LLM
            prediction = self._generate_prediction_with_llm(new_meal, similar_meals, outcomes, correlation)
            
            return prediction
            
        except Exception as e:
            print(f"⚠️ Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "prediction": "Unable to generate prediction",
                "confidence": 0,
                "reasoning": str(e)
            }
    
    def _find_similar_meals(self, new_meal: Meal, past_meals: List[Meal]) -> List[Meal]:
        """Find meals similar to the new meal"""
        similar = []
        
        # Extract foods from new meal
        new_foods = set()
        if new_meal.detected_foods:
            import json
            foods = json.loads(new_meal.detected_foods) if isinstance(new_meal.detected_foods, str) else new_meal.detected_foods
            for food in foods:
                # Handle both string and dict formats
                if isinstance(food, dict):
                    food_name = food.get('name', food.get('food', str(food)))
                else:
                    food_name = str(food)
                if food_name:
                    new_foods.add(food_name.lower())
        
        # Find meals with similar foods or similar gluten risk
        for meal in past_meals:
            similarity_score = 0
            
            # Check gluten risk similarity (within 20 points)
            if abs(meal.gluten_risk_score - new_meal.gluten_risk_score) <= 20:
                similarity_score += 1
            
            # Check food overlap
            if meal.detected_foods:
                import json
                foods = json.loads(meal.detected_foods) if isinstance(meal.detected_foods, str) else meal.detected_foods
                meal_foods = set()
                for food in foods:
                    # Handle both string and dict formats
                    if isinstance(food, dict):
                        food_name = food.get('name', food.get('food', str(food)))
                    else:
                        food_name = str(food)
                    if food_name:
                        meal_foods.add(food_name.lower())
                overlap = len(new_foods & meal_foods)
                if overlap > 0:
                    similarity_score += overlap
            
            if similarity_score > 0:
                similar.append((meal, similarity_score))
        
        # Sort by similarity and return top 5
        similar.sort(key=lambda x: x[1], reverse=True)
        return [meal for meal, _ in similar[:5]]
    
    def _get_past_outcomes(self, similar_meals: List[Meal], past_symptoms: List[Symptom]) -> Dict[str, Any]:
        """Get symptom outcomes for similar meals"""
        outcomes = {
            "symptom_count": 0,
            "avg_severity": 0,
            "common_symptoms": {},
            "time_lag_hours": []
        }
        
        if not similar_meals:
            return outcomes
        
        # Check symptoms within 24 hours of each similar meal
        for meal in similar_meals:
            meal_time = meal.timestamp
            cutoff = meal_time + timedelta(hours=24)
            
            for symptom in past_symptoms:
                if meal_time <= symptom.timestamp <= cutoff:
                    outcomes["symptom_count"] += 1
                    outcomes["avg_severity"] += symptom.severity
                    
                    symptom_type = symptom.symptom_type or "unknown"
                    outcomes["common_symptoms"][symptom_type] = outcomes["common_symptoms"].get(symptom_type, 0) + 1
                    
                    time_lag = (symptom.timestamp - meal_time).total_seconds() / 3600
                    outcomes["time_lag_hours"].append(time_lag)
        
        if outcomes["symptom_count"] > 0:
            outcomes["avg_severity"] /= outcomes["symptom_count"]
            if outcomes["time_lag_hours"]:
                outcomes["avg_time_lag"] = sum(outcomes["time_lag_hours"]) / len(outcomes["time_lag_hours"])
        
        return outcomes
    
    def _generate_prediction_with_llm(self, new_meal: Meal, similar_meals: List[Meal], 
                                     outcomes: Dict[str, Any], correlation: Optional[float]) -> Dict[str, Any]:
        """Use LLM to generate prediction with reasoning"""
        try:
            # Build context
            foods_str = "None"
            if new_meal.detected_foods:
                import json
                foods = json.loads(new_meal.detected_foods) if isinstance(new_meal.detected_foods, str) else new_meal.detected_foods
                foods_str = ", ".join(foods)
            
            similar_count = len(similar_meals)
            symptom_probability = min(100, (outcomes["symptom_count"] / max(1, similar_count)) * 100) if similar_count > 0 else 0
            
            context_str = f"""New Meal:
- Description: {new_meal.description}
- Foods: {foods_str}
- Gluten Risk: {new_meal.gluten_risk_score}/100

Historical Patterns:
- Similar meals found: {similar_count}
- Symptoms after similar meals: {outcomes['symptom_count']} times
- Average severity: {outcomes['avg_severity']:.1f}/10
- Common symptoms: {', '.join(list(outcomes['common_symptoms'].keys())[:3]) if outcomes['common_symptoms'] else 'None'}
- Average time lag: {outcomes.get('avg_time_lag', 0):.1f} hours
- Overall correlation: {correlation}% if available

Estimated probability of symptoms: {symptom_probability:.0f}%"""
            
            prompt = f"""Based on this meal and historical patterns, predict likely symptoms.

{context_str}

Generate a prediction with:
1. Likely symptoms (if any)
2. Probability percentage (0-100%)
3. Time window (when symptoms might appear)
4. Brief reasoning (why this prediction)

Format as JSON:
{{
  "symptoms": ["symptom1", "symptom2"],
  "probability": 75,
  "time_window_hours": 3,
  "reasoning": "Brief explanation"
}}

If probability is low (<30%), set symptoms to empty array and explain why.

Respond with ONLY valid JSON, nothing else."""
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a health prediction system. Generate symptom predictions based on meal data and historical patterns. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                prediction_data = json.loads(json_match.group())
                
                return {
                    "prediction": ", ".join(prediction_data.get("symptoms", [])) or "Low probability of symptoms",
                    "confidence": prediction_data.get("probability", 0),
                    "time_window_hours": prediction_data.get("time_window_hours", 3),
                    "reasoning": prediction_data.get("reasoning", "Based on historical patterns")
                }
            
            # Fallback
            return {
                "prediction": "Unable to parse prediction",
                "confidence": 0,
                "reasoning": "Error parsing LLM response"
            }
            
        except Exception as e:
            print(f"⚠️ LLM prediction error: {e}")
            return {
                "prediction": "Error generating prediction",
                "confidence": 0,
                "reasoning": str(e)
            }

