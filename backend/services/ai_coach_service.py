"""AI Coach Service for conversational health coaching with RAG"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from groq import Groq
from config import settings
from models import Meal, Symptom
from services.analysis_service import AnalysisService
from services.retrieval_service import RetrievalService
from sqlalchemy.orm import Session

class AICoachService:
    """Service for AI-powered health coaching chat"""
    
    def __init__(self):
        """Initialize AI Coach service"""
        self.groq_client = None
        # Clean API key thoroughly - remove BOM, whitespace, hidden chars
        api_key = (settings.GROQ_API_KEY or "").strip()
        api_key = api_key.strip('\ufeff').strip('\u200b').strip('\n').strip('\r').strip('"').strip("'")
        
        if api_key and api_key.startswith('gsk_'):
            try:
                self.groq_client = Groq(api_key=api_key)
                print("✅ Groq API initialized for AI Coach")
            except Exception as e:
                print(f"⚠️ Could not initialize Groq for AI Coach: {e}")
                self.groq_client = None
        elif api_key:
            print(f"⚠️ GROQ_API_KEY format invalid (should start with 'gsk_')")
            print(f"   Key preview: '{api_key[:20]}...' (length: {len(api_key)})")
            self.groq_client = None
        else:
            print("⚠️ GROQ_API_KEY is empty or not set. AI Coach will not be available.")
        
        self.analysis_service = AnalysisService()
        self.retrieval_service = RetrievalService()
    
    def get_user_context(self, meals: List[Meal], symptoms: List[Symptom], days: int = 7) -> Dict[str, Any]:
        """Get user's recent data for context"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_meals = [m for m in meals if m.timestamp >= cutoff_date]
        recent_symptoms = [s for s in symptoms if s.timestamp >= cutoff_date]
        
        # Calculate stats
        avg_gluten_risk = sum(m.gluten_risk_score for m in recent_meals) / len(recent_meals) if recent_meals else 0
        avg_severity = sum(s.severity for s in recent_symptoms) / len(recent_symptoms) if recent_symptoms else 0
        
        # Get correlation if enough data
        correlation = None
        if len(meals) >= 10 and len(symptoms) >= 10:
            try:
                correlation_analysis = self.analysis_service.calculate_correlation(meals, symptoms)
                correlation = correlation_analysis.correlation_score
            except:
                pass
        
        # Get common foods
        food_counts = {}
        for meal in recent_meals:
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
                        food_counts[food_name] = food_counts.get(food_name, 0) + 1
        
        common_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Get common symptoms
        symptom_counts = {}
        for symptom in recent_symptoms:
            symptom_type = symptom.symptom_type or "unknown"
            symptom_counts[symptom_type] = symptom_counts.get(symptom_type, 0) + 1
        
        common_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "recent_meals_count": len(recent_meals),
            "recent_symptoms_count": len(recent_symptoms),
            "avg_gluten_risk": round(avg_gluten_risk, 1),
            "avg_severity": round(avg_severity, 1),
            "correlation": correlation,
            "common_foods": [f[0] for f in common_foods],
            "common_symptoms": [s[0] for s in common_symptoms],
            "total_meals": len(meals),
            "total_symptoms": len(symptoms)
        }
    
    def chat(self, question: str, meals: List[Meal], symptoms: List[Symptom], db: Optional[Session] = None, user_id: int = 1) -> Tuple[str, Dict[str, int]]:
        """
        Generate AI coach response based on user question and data (RAG-enhanced)
        
        Returns: (answer, retrieval_stats)
        """
        retrieval_stats = {"meals_retrieved": 0, "symptoms_retrieved": 0, "correlations_retrieved": 0, "total_items_retrieved": 0}
        
        if not self.groq_client:
            api_key = (settings.GROQ_API_KEY or "").strip().strip('\ufeff')
            if not api_key:
                return ("I'm sorry, the AI Coach is currently unavailable. The GROQ_API_KEY is not configured. Please add GROQ_API_KEY=your_api_key to your .env file in the backend directory.", retrieval_stats)
            elif not api_key.startswith('gsk_'):
                return ("I'm sorry, the AI Coach is currently unavailable. The GROQ_API_KEY format appears invalid (should start with 'gsk_'). Please check your .env file.", retrieval_stats)
            else:
                return ("I'm sorry, the AI Coach is currently unavailable. The Groq API key appears to be invalid or expired. Please:\n1. Check your API key at https://console.groq.com/\n2. Generate a new API key if needed\n3. Update GROQ_API_KEY in your .env file\n4. Restart the backend server", retrieval_stats)
        
        try:
            # Get user context
            context = self.get_user_context(meals, symptoms)
            
            # RAG: Retrieve relevant context from knowledge base
            rag_context = ""
            retrieved_meals = []
            retrieved_symptoms = []
            correlated_pairs = []
            
            if db:
                try:
                    # Extract query keywords from question
                    query_lower = question.lower()
                    keywords = []
                    symptom_keywords = ["bloating", "pain", "nausea", "fatigue", "headache", "diarrhea", "constipation"]
                    food_keywords = ["bread", "pizza", "pasta", "roti", "naan", "rice", "wheat"]
                    
                    for kw in symptom_keywords + food_keywords:
                        if kw in query_lower:
                            keywords.append(kw)
                    
                    # Retrieve high-gluten meals (most relevant for gluten questions)
                    retrieved_meals = self.retrieval_service.retrieve_relevant_meals(
                        db, user_id, 
                        query_keywords=keywords if keywords else None,
                        gluten_risk_min=70,
                        days_back=30,
                        limit=5
                    )
                    
                    # Retrieve severe symptoms
                    retrieved_symptoms = self.retrieval_service.retrieve_relevant_symptoms(
                        db, user_id,
                        query_keywords=keywords if keywords else None,
                        severity_min=6,
                        days_back=30,
                        limit=5
                    )
                    
                    # Retrieve correlated meal-symptom pairs
                    correlated_pairs = self.retrieval_service.retrieve_correlated_pairs(
                        db, user_id,
                        time_window_hours=6,
                        days_back=30,
                        limit=3
                    )
                    
                    # Format retrieved context for LLM
                    rag_context = self.retrieval_service.format_retrieval_context(
                        retrieved_meals,
                        retrieved_symptoms,
                        correlated_pairs
                    )
                    
                    # Get retrieval stats for UI
                    retrieval_stats = self.retrieval_service.get_retrieval_stats(
                        retrieved_meals,
                        retrieved_symptoms,
                        correlated_pairs
                    )
                    
                    if retrieval_stats["total_items_retrieved"] > 0:
                        rag_context = f"\n[RAG KNOWLEDGE BASE RETRIEVAL]\n{rag_context}\n"
                    
                except Exception as e:
                    print(f"⚠️ RAG retrieval error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Build context string
            context_str = f"""User's Health Data Summary:
- Recent meals (last 7 days): {context['recent_meals_count']}
- Recent symptoms (last 7 days): {context['recent_symptoms_count']}
- Average gluten risk: {context['avg_gluten_risk']}/100
- Average symptom severity: {context['avg_severity']}/10
- Correlation (if available): {context['correlation']}% if calculated
- Most common foods: {', '.join(context['common_foods']) if context['common_foods'] else 'None'}
- Most common symptoms: {', '.join(context['common_symptoms']) if context['common_symptoms'] else 'None'}
- Total meals logged: {context['total_meals']}
- Total symptoms logged: {context['total_symptoms']}"""
            
            # Create prompt with RAG-enhanced context
            prompt = f"""You are a compassionate, knowledgeable health coach helping someone track gluten intolerance patterns. 

{context_str}

{rag_context if rag_context else ''}

User's Question: "{question}"

Instructions:
- Provide empathetic, helpful advice based on the user's actual data
- Reference specific patterns you see in their data (e.g., "I notice you've had bloating 3 times this week after eating bread products")
- Give actionable recommendations (e.g., "Try avoiding gluten for 3 days and see if symptoms improve")
- Be encouraging and supportive
- Use plain language, avoid medical jargon unless necessary
- Keep response concise (2-4 sentences, max 200 words)
- If correlation data is available, mention it naturally
- Focus on what the data shows, not speculation

Respond as a friendly health coach would, using "you" and "your" to address the user directly."""
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a compassionate health coach specializing in gluten intolerance and food sensitivity tracking. You help users understand their health data and make informed decisions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7  # Slightly higher for more natural conversation
            )
            
            answer = response.choices[0].message.content.strip()
            return (answer, retrieval_stats)
            
        except Exception as e:
            error_str = str(e)
            print(f"⚠️ AI Coach error: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if it's an authentication error
            if "401" in error_str or "invalid_api_key" in error_str or "Invalid API Key" in error_str:
                return ("I'm sorry, I'm unable to respond right now. Your Groq API key appears to be invalid or expired. Please:\n\n1. Visit https://console.groq.com/\n2. Check your API keys section\n3. Generate a new API key if needed\n4. Update GROQ_API_KEY in backend/.env file\n5. Restart the backend server\n\nOnce the key is updated, I'll be ready to help!", retrieval_stats)
            else:
                return (f"I'm sorry, I encountered an error while processing your question. Please try again. If the issue persists, check the server logs for details.", retrieval_stats)

