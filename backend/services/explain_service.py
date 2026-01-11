"""Explain Service for explaining results, correlations, and data points"""
from typing import Dict, Any, Optional
from groq import Groq
from config import settings
from models import Meal, Symptom

class ExplainService:
    """Service for explaining results using LLM"""
    
    def __init__(self):
        """Initialize Explain service"""
        self.groq_client = None
        api_key = (settings.GROQ_API_KEY or "").strip().strip('\ufeff').strip('\u200b')
        if api_key and api_key.startswith('gsk_'):
            try:
                self.groq_client = Groq(api_key=api_key)
                print("✅ Groq API initialized for Explain service")
            except Exception as e:
                print(f"⚠️ Could not initialize Groq for Explain: {e}")
                import traceback
                traceback.print_exc()
        else:
            if api_key:
                print(f"⚠️ GROQ_API_KEY format invalid (should start with 'gsk_'). Explain features will not be available.")
            else:
                print("⚠️ GROQ_API_KEY is empty or not set. Explain features will not be available.")
    
    def explain_gluten_risk(self, food_name: str, gluten_risk: float, meal_description: Optional[str] = None) -> str:
        """Explain why a food has a specific gluten risk score"""
        if not self.groq_client:
            return f"This food has a gluten risk score of {gluten_risk}/100. Higher scores indicate more gluten content."
        
        try:
            prompt = f"""Explain why "{food_name}" has a gluten risk score of {gluten_risk}/100.

Context:
- Food: {food_name}
- Gluten Risk: {gluten_risk}/100
- Meal description: {meal_description or 'Not provided'}

Requirements:
- Explain in 2-3 sentences
- Be specific about gluten sources (e.g., "wheat flour", "barley", "rye")
- Explain the risk level (0-30 = low, 31-70 = medium, 71-100 = high)
- Use plain language, avoid jargon
- Be informative and helpful

Example for pizza (100/100):
"Pizza has a very high gluten risk (100/100) because it's made with wheat flour dough, which contains gluten. The crust, which is the main component of pizza, is typically made from refined wheat flour that has a high gluten content. This makes pizza unsafe for individuals with celiac disease or gluten sensitivity."

Respond with ONLY the explanation, nothing else."""
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a nutritionist explaining gluten risk scores to users tracking their food intake."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3  # Lower temperature for more factual, consistent explanations
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
            
        except Exception as e:
            print(f"⚠️ Explain gluten risk error: {e}")
            return f"This food has a gluten risk score of {gluten_risk}/100. Higher scores indicate more gluten content."
    
    def explain_correlation(self, correlation_score: float, p_value: Optional[float] = None, 
                           total_meals: int = 0, total_symptoms: int = 0) -> str:
        """Explain what a correlation score means"""
        if not self.groq_client:
            return f"Your correlation score is {correlation_score}%. This indicates the strength of the relationship between gluten intake and symptoms."
        
        try:
            significance = ""
            if p_value is not None:
                if p_value < 0.001:
                    significance = "highly statistically significant (p<0.001)"
                elif p_value < 0.05:
                    significance = "statistically significant (p<0.05)"
                else:
                    significance = "not statistically significant"
            
            prompt = f"""Explain what a correlation score of {correlation_score}% means in the context of gluten intolerance tracking.

Context:
- Correlation Score: {correlation_score}%
- Statistical Significance: {significance if significance else 'Not calculated'}
- Data Points: {total_meals} meals, {total_symptoms} symptoms

Requirements:
- Explain in 2-3 sentences
- Explain what the percentage means (0% = no relationship, 100% = perfect relationship)
- Mention if it's statistically significant
- Give practical interpretation (e.g., "This suggests a strong relationship between gluten and your symptoms")
- Use plain language, avoid complex statistics jargon
- Be encouraging and helpful

Example for 85% correlation:
"An 85% correlation means there's a strong relationship between your gluten intake and symptoms. This suggests that when you eat high-gluten foods, you're likely to experience symptoms. The relationship is statistically significant, meaning it's unlikely to be due to chance. This is strong evidence that you may have gluten sensitivity."

Respond with ONLY the explanation, nothing else."""
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a health data analyst explaining correlation results to users in plain language."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.3
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
            
        except Exception as e:
            print(f"⚠️ Explain correlation error: {e}")
            return f"Your correlation score is {correlation_score}%. This indicates the strength of the relationship between gluten intake and symptoms."
    
    def explain_data_point(self, meal: Optional[Meal] = None, symptom: Optional[Symptom] = None, 
                          context: Optional[Dict[str, Any]] = None) -> str:
        """Explain a specific data point in context"""
        if not self.groq_client:
            return "This data point shows your meal or symptom entry."
        
        try:
            if meal:
                prompt = f"""Explain this meal entry in the context of gluten tracking:

Meal: {meal.description}
Gluten Risk: {meal.gluten_risk_score}/100
Time: {meal.timestamp}
Foods Detected: {meal.detected_foods or 'None'}

{('Context: ' + str(context)) if context else ''}

Explain:
- What this meal means for gluten tracking
- Why the gluten risk is what it is
- What to watch for (symptoms that might follow)
- Keep it to 2-3 sentences, plain language"""
            
            elif symptom:
                prompt = f"""Explain this symptom entry in the context of gluten tracking:

Symptom: {symptom.description}
Severity: {symptom.severity}/10
Type: {symptom.symptom_type or 'Unknown'}
Time: {symptom.timestamp}

{('Context: ' + str(context)) if context else ''}

Explain:
- What this symptom might indicate
- How it relates to gluten tracking
- What patterns to look for
- Keep it to 2-3 sentences, plain language"""
            
            else:
                return "No data point provided."
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a health coach explaining data points to users tracking gluten intolerance."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.4
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
            
        except Exception as e:
            print(f"⚠️ Explain data point error: {e}")
            return "This data point shows your meal or symptom entry."

