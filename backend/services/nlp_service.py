"""NLP Service for text analysis"""
import re
import json
from typing import List, Dict, Any, Optional
import spacy
from transformers import pipeline
from groq import Groq
from config import settings

class NLPService:
    """Natural Language Processing service for symptom and food analysis"""
    
    def __init__(self):
        """Initialize NLP models"""
        # Load spaCy model (will download if not present)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Sentiment analysis model (lightweight)
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
        except Exception as e:
            print(f"Warning: Could not load sentiment model: {e}")
            self.sentiment_analyzer = None
        
        # Initialize Groq client for LLM validation
        self.groq_client = None
        if settings.GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
                print("✅ Groq API initialized for NLP validation")
            except Exception as e:
                print(f"⚠️ Could not initialize Groq for NLP: {e}")
        
        # Common symptom keywords
        self.symptom_keywords = {
            "bloating": ["bloat", "bloated", "swollen", "distended", "gas", "gassy"],
            "pain": ["pain", "ache", "hurt", "sore", "cramp", "cramping"],
            "diarrhea": ["diarrhea", "loose stool", "watery stool", "runs"],
            "constipation": ["constipated", "constipation", "backed up", "hard stool"],
            "nausea": ["nausea", "nauseous", "queasy", "sick to stomach"],
            "fatigue": ["tired", "fatigue", "exhausted", "drained", "weak"],
            "headache": ["headache", "head pain", "migraine"],
            "brain_fog": ["brain fog", "foggy", "confused", "unfocused", "difficulty concentrating"],
            "mood": ["anxious", "anxiety", "depressed", "depression", "irritable", "mood swing"],
            "skin": ["rash", "itchy", "eczema", "hives", "skin issue"]
        }
        
        # Severity keywords
        self.severity_map = {
            "mild": 3,
            "slight": 3,
            "minor": 3,
            "moderate": 5,
            "medium": 5,
            "bad": 6,
            "severe": 8,
            "terrible": 9,
            "excruciating": 10,
            "unbearable": 10,
            "horrible": 9,
            "awful": 8,
            "intense": 7
        }
        
        # Food keywords
        self.food_patterns = [
            r"\b(bread|toast|sandwich|bagel|baguette|roll)\b",
            r"\b(pasta|spaghetti|noodles|macaroni|linguine)\b",
            r"\b(pizza|pie)\b",
            r"\b(cereal|granola|oats)\b",
            r"\b(cake|cookie|pastry|muffin|donut|croissant)\b",
            r"\b(beer|ale|lager)\b",
            r"\b(rice|quinoa|salad|fruit|vegetable)\b",
            r"\b(chicken|beef|pork|fish|salmon|tuna|turkey)\b",
            r"\b(cheese|yogurt|milk|dairy)\b",
            r"\b(soup|stew|broth)\b"
        ]
    
    def analyze_symptom(self, text: str) -> Dict[str, Any]:
        """
        Analyze symptom text and extract:
        - Symptom type
        - Severity
        - Sentiment
        - Time context
        """
        text_lower = text.lower()
        
        # Extract symptom type
        symptom_type = self._extract_symptom_type(text_lower)
        
        # Extract severity
        severity = self._extract_severity(text_lower)
        
        # Sentiment analysis
        sentiment_score = self._analyze_sentiment(text)
        
        # Time context extraction
        time_context = self._extract_time_context(text_lower)
        
        # Extract all symptoms (can be multiple)
        extracted_symptoms = self._extract_all_symptoms(text_lower)
        
        return {
            "symptom_type": symptom_type,
            "severity": severity,
            "sentiment_score": sentiment_score,
            "time_context": time_context,
            "extracted_symptoms": extracted_symptoms
        }
    
    def _extract_symptom_type(self, text: str) -> str:
        """Extract primary symptom type"""
        for symptom_type, keywords in self.symptom_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return symptom_type
        return "general"
    
    def _extract_all_symptoms(self, text: str) -> List[Dict[str, str]]:
        """Extract all symptoms mentioned"""
        found_symptoms = []
        for symptom_type, keywords in self.symptom_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    found_symptoms.append({
                        "type": symptom_type,
                        "mention": keyword
                    })
                    break  # Only add once per type
        return found_symptoms
    
    def _extract_severity(self, text: str) -> float:
        """Extract severity score (0-10)"""
        # Check for explicit numbers
        number_match = re.search(r'\b(\d+)/10\b', text)
        if number_match:
            return float(number_match.group(1))
        
        # Check for severity keywords
        for keyword, score in self.severity_map.items():
            if keyword in text:
                return float(score)
        
        # Default moderate severity
        return 5.0
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment (-1 to 1)"""
        if not self.sentiment_analyzer:
            return 0.0
        
        try:
            result = self.sentiment_analyzer(text[:512])[0]  # Limit text length
            score = result["score"]
            if result["label"] == "NEGATIVE":
                return -score
            return score
        except Exception:
            return 0.0
    
    def _extract_time_context(self, text: str) -> str:
        """Extract time context (e.g., 'after lunch', '3 hours after eating')"""
        # Common time patterns
        time_patterns = [
            r"(\d+\s+(?:hour|hr)s?\s+(?:after|later))",
            r"(after\s+(?:breakfast|lunch|dinner|eating|meal))",
            r"(before\s+(?:breakfast|lunch|dinner|eating|meal))",
            r"(during\s+(?:breakfast|lunch|dinner|eating|meal))",
            r"(in the\s+(?:morning|afternoon|evening|night))"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def extract_food_entities(self, text: str) -> List[str]:
        """Extract food items from text with enhanced desi food recognition"""
        text_lower = text.lower()
        foods = []
        
        # Priority 1: Check for desi foods explicitly (most important)
        desi_foods = [
            "roti", "chapati", "chappati", "chapathi", "naan", "paratha", "parantha",
            "puri", "poori", "bhatura", "kulcha", "samosa", "pakora", "kachori",
            "biryani", "pulao", "dal", "daal", "curry", "sabzi", "raita", "paneer",
            "aloo", "gobi", "matar", "palak", "bhaji", "bonda", "idli", "dosa",
            "vada", "upma", "poha", "khichdi", "halwa", "ladoo", "jalebi"
        ]
        
        for desi_food in desi_foods:
            if desi_food in text_lower:
                foods.append(desi_food)
        
        # Priority 2: Check for common western foods
        western_foods = [
            "bread", "sandwich", "pizza", "pasta", "burger", "noodles",
            "cake", "cookie", "pancake", "waffle", "bagel", "croissant",
            "rice", "egg", "eggs", "chicken", "fish", "meat", "salad"
        ]
        
        for western_food in western_foods:
            if western_food in text_lower:
                foods.append(western_food)
        
        # Priority 3: Use spaCy NER
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG", "GPE"]:  # Sometimes foods are labeled as products
                foods.append(ent.text.lower())
        
        # Priority 4: Use regex patterns for common foods
        for pattern in self.food_patterns:
            matches = re.findall(pattern, text_lower)
            foods.extend(matches)
        
        # Priority 5: Extract nouns that might be foods (last resort)
        for token in doc:
            if token.pos_ == "NOUN" and len(token.text) > 3:
                # Filter out common non-food nouns
                non_food_words = ["time", "hour", "minute", "day", "week", "morning", "evening", "lunch", "dinner", "breakfast"]
                if token.text.lower() not in non_food_words:
                    foods.append(token.text.lower())
        
        # Remove duplicates
        foods = list(set(foods))
        
        # Validate with Groq LLM if available (cross-validation)
        if self.groq_client and foods:
            try:
                validated_foods = self._validate_foods_with_groq(text, foods)
                if validated_foods:
                    print(f"🔍 Groq validation: {foods} → {validated_foods}")
                    return validated_foods
            except Exception as e:
                print(f"⚠️ Groq validation failed, using NLP results: {e}")
        
        return foods
    
    def _validate_foods_with_groq(self, text: str, nlp_foods: List[str]) -> Optional[List[str]]:
        """
        Validate and enhance food extraction using Groq LLM
        This demonstrates LLM-based validation in NLP pipeline
        """
        try:
            prompt = f"""Analyze this meal description and extract ALL food items mentioned.
Text: "{text}"

Previously detected foods (may be incomplete): {', '.join(nlp_foods) if nlp_foods else 'none'}

Extract ALL foods including:
- Desi/South Asian: roti, chapati, naan, paratha, samosa, pakora, biryani, dal, curry, etc.
- Western: bread, pizza, pasta, sandwich, burger, etc.
- Ingredients: eggs, chicken, rice, vegetables, etc.

Respond ONLY with a JSON array of food names in lowercase, nothing else:
["food1", "food2", "food3"]

Example: ["roti", "chicken", "curry"] or ["bread", "chicken", "sandwich"]"""

            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Fast model for validation
                messages=[
                    {"role": "system", "content": "You are a food extraction expert. Extract all food items from meal descriptions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON array
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                foods = json.loads(json_match.group())
                if isinstance(foods, list) and all(isinstance(f, str) for f in foods):
                    return [f.lower().strip() for f in foods if f.strip()]
            
            return None
        except Exception as e:
            print(f"⚠️ Groq validation error: {e}")
            return None

