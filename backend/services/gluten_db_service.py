"""Gluten database service for food risk mappings"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models import GlutenDatabase
from groq import Groq
from config import settings

# Comprehensive gluten risk database
GLUTEN_DATABASE = [
    # VERY HIGH RISK (90-100) - Contains gluten
    {"food_name": "bread", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": ["toast", "loaf", "baguette"]},
    {"food_name": "wheat bread", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": []},
    {"food_name": "white bread", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": []},
    {"food_name": "whole wheat bread", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": []},
    {"food_name": "pasta", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": ["spaghetti", "noodles", "macaroni", "penne"]},
    {"food_name": "pizza", "gluten_risk": 100, "category": "processed", "hidden_source": False, "aliases": ["pizza pie"]},
    {"food_name": "bagel", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": []},
    {"food_name": "croissant", "gluten_risk": 100, "category": "pastry", "hidden_source": False, "aliases": []},
    {"food_name": "muffin", "gluten_risk": 95, "category": "pastry", "hidden_source": False, "aliases": []},
    {"food_name": "donut", "gluten_risk": 95, "category": "pastry", "hidden_source": False, "aliases": ["doughnut"]},
    {"food_name": "cake", "gluten_risk": 95, "category": "dessert", "hidden_source": False, "aliases": []},
    {"food_name": "cookie", "gluten_risk": 95, "category": "dessert", "hidden_source": False, "aliases": ["biscuit"]},
    {"food_name": "pancake", "gluten_risk": 95, "category": "breakfast", "hidden_source": False, "aliases": []},
    {"food_name": "waffle", "gluten_risk": 95, "category": "breakfast", "hidden_source": False, "aliases": []},
    {"food_name": "cereal", "gluten_risk": 90, "category": "grain", "hidden_source": False, "aliases": []},
    {"food_name": "granola", "gluten_risk": 85, "category": "grain", "hidden_source": False, "aliases": []},
    {"food_name": "cracker", "gluten_risk": 95, "category": "snack", "hidden_source": False, "aliases": []},
    {"food_name": "pretzel", "gluten_risk": 100, "category": "snack", "hidden_source": False, "aliases": []},
    {"food_name": "ramen", "gluten_risk": 95, "category": "grain", "hidden_source": False, "aliases": ["instant noodles"]},
    {"food_name": "dumpling", "gluten_risk": 90, "category": "processed", "hidden_source": False, "aliases": []},
    
    # VERY HIGH RISK (90-100) - Desi/South Asian Foods (ALL contain wheat flour)
    {"food_name": "roti", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": ["chapati", "chappati", "chapathi", "phulka"], "description": "Made from whole wheat flour (atta)"},
    {"food_name": "naan", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": ["tandoori naan", "garlic naan", "butter naan"], "description": "Leavened flatbread made from wheat flour"},
    {"food_name": "paratha", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": ["parantha", "parota", "laccha paratha", "aloo paratha", "gobi paratha", "paneer paratha"], "description": "Layered flatbread made from wheat flour"},
    {"food_name": "puri", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": ["poori"], "description": "Deep-fried bread made from wheat flour"},
    {"food_name": "bhatura", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": ["bhatoora"], "description": "Puffed fried bread made from wheat flour"},
    {"food_name": "kulcha", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": ["amritsari kulcha"], "description": "Leavened flatbread made from wheat flour"},
    {"food_name": "rumali roti", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": ["roomali roti"], "description": "Thin flatbread made from wheat flour"},
    {"food_name": "tandoori roti", "gluten_risk": 100, "category": "grain", "hidden_source": False, "aliases": [], "description": "Tandoor-baked flatbread made from wheat flour"},
    {"food_name": "samosa", "gluten_risk": 90, "category": "snack", "hidden_source": False, "aliases": ["samosas"], "description": "Fried pastry with wheat flour wrapper"},
    {"food_name": "kachori", "gluten_risk": 90, "category": "snack", "hidden_source": False, "aliases": ["kachoris"], "description": "Fried pastry with wheat flour wrapper"},
    {"food_name": "mathri", "gluten_risk": 90, "category": "snack", "hidden_source": False, "aliases": ["mathris"], "description": "Crispy fried snack made from wheat flour"},
    {"food_name": "pakora", "gluten_risk": 85, "category": "snack", "hidden_source": False, "aliases": ["pakoras", "bhajji"], "description": "Fritters with wheat flour batter"},
    {"food_name": "bhaji", "gluten_risk": 85, "category": "snack", "hidden_source": False, "aliases": ["onion bhaji", "vegetable bhaji"], "description": "Fritters with wheat flour batter"},
    {"food_name": "bonda", "gluten_risk": 85, "category": "snack", "hidden_source": False, "aliases": ["bondas"], "description": "Fried snack with wheat flour batter"},
    
    # HIGH RISK (70-89) - Often contains gluten
    {"food_name": "beer", "gluten_risk": 90, "category": "beverage", "hidden_source": False, "aliases": ["ale", "lager"]},
    {"food_name": "soy sauce", "gluten_risk": 85, "category": "sauce", "hidden_source": True, "aliases": ["shoyu"], "description": "Usually contains wheat"},
    {"food_name": "fried chicken", "gluten_risk": 80, "category": "processed", "hidden_source": False, "aliases": []},
    {"food_name": "breaded", "gluten_risk": 90, "category": "processed", "hidden_source": False, "aliases": ["battered"]},
    {"food_name": "tortilla", "gluten_risk": 75, "category": "grain", "hidden_source": False, "aliases": ["flour tortilla"], "description": "Flour tortillas contain gluten, corn tortillas don't"},
    {"food_name": "wrap", "gluten_risk": 80, "category": "grain", "hidden_source": False, "aliases": []},
    {"food_name": "hamburger", "gluten_risk": 85, "category": "processed", "hidden_source": False, "aliases": ["burger"]},
    {"food_name": "hot dog", "gluten_risk": 75, "category": "processed", "hidden_source": False, "aliases": []},
    {"food_name": "gravy", "gluten_risk": 70, "category": "sauce", "hidden_source": True, "aliases": [], "description": "Usually thickened with flour"},
    {"food_name": "soup", "gluten_risk": 60, "category": "processed", "hidden_source": True, "aliases": [], "description": "May contain flour or barley"},
    
    # MEDIUM RISK (30-69) - May contain hidden gluten
    {"food_name": "oatmeal", "gluten_risk": 50, "category": "grain", "hidden_source": True, "aliases": ["oats"], "description": "Often cross-contaminated unless certified GF"},
    {"food_name": "french fries", "gluten_risk": 40, "category": "processed", "hidden_source": True, "aliases": ["fries"], "description": "May be coated or cross-contaminated"},
    {"food_name": "processed meat", "gluten_risk": 45, "category": "processed", "hidden_source": True, "aliases": ["deli meat", "lunch meat"]},
    {"food_name": "salad dressing", "gluten_risk": 35, "category": "sauce", "hidden_source": True, "aliases": []},
    {"food_name": "ketchup", "gluten_risk": 30, "category": "sauce", "hidden_source": True, "aliases": []},
    {"food_name": "mustard", "gluten_risk": 30, "category": "sauce", "hidden_source": True, "aliases": []},
    
    # LOW RISK (10-29) - Usually safe but check labels
    {"food_name": "corn", "gluten_risk": 10, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "corn tortilla", "gluten_risk": 10, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "potato", "gluten_risk": 10, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "sweet potato", "gluten_risk": 10, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "yogurt", "gluten_risk": 15, "category": "dairy", "hidden_source": True, "aliases": [], "description": "May contain additives"},
    {"food_name": "cheese", "gluten_risk": 10, "category": "dairy", "hidden_source": False, "aliases": []},
    {"food_name": "milk", "gluten_risk": 5, "category": "dairy", "hidden_source": False, "aliases": []},
    
    # VERY LOW RISK (0-9) - Naturally gluten-free
    {"food_name": "rice", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": ["brown rice", "white rice", "basmati rice", "jeera rice"]},
    {"food_name": "pulao", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": ["pulav", "pilaf"], "description": "Rice-based dish, gluten-free"},
    {"food_name": "biryani", "gluten_risk": 30, "category": "safe", "hidden_source": False, "aliases": ["biryani rice"], "description": "Rice-based, but often served with naan/roti"},
    {"food_name": "dal", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": ["daal", "lentil", "lentils", "dal fry", "dal tadka"], "description": "Lentil-based, naturally gluten-free"},
    {"food_name": "curry", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": ["sabzi", "vegetable curry", "chicken curry", "mutton curry", "fish curry"], "description": "Usually gluten-free unless thickened with flour"},
    {"food_name": "raita", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": ["dahi raita"], "description": "Yogurt-based, gluten-free"},
    {"food_name": "dahi", "gluten_risk": 5, "category": "dairy", "hidden_source": False, "aliases": ["yogurt"], "description": "Plain yogurt, gluten-free"},
    {"food_name": "lassi", "gluten_risk": 5, "category": "beverage", "hidden_source": False, "aliases": ["sweet lassi", "mango lassi"], "description": "Yogurt-based drink, gluten-free"},
    {"food_name": "paneer", "gluten_risk": 10, "category": "dairy", "hidden_source": False, "aliases": ["paneer curry", "paneer tikka", "paneer masala"], "description": "Indian cheese, usually gluten-free"},
    {"food_name": "aloo", "gluten_risk": 10, "category": "safe", "hidden_source": False, "aliases": ["potato", "aloo gobi", "aloo matar"], "description": "Potato-based, gluten-free"},
    {"food_name": "kachumber", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": [], "description": "Fresh salad, gluten-free"},
    {"food_name": "quinoa", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "meat", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "chicken", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "beef", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "pork", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "fish", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": ["salmon", "tuna", "cod"]},
    {"food_name": "egg", "gluten_risk": 5, "category": "safe", "hidden_source": False, "aliases": ["eggs"]},
    {"food_name": "fruit", "gluten_risk": 0, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "vegetable", "gluten_risk": 0, "category": "safe", "hidden_source": False, "aliases": ["veggies"]},
    {"food_name": "salad", "gluten_risk": 10, "category": "safe", "hidden_source": False, "aliases": [], "description": "Check dressing"},
    {"food_name": "apple", "gluten_risk": 0, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "banana", "gluten_risk": 0, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "orange", "gluten_risk": 0, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "broccoli", "gluten_risk": 0, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "carrot", "gluten_risk": 0, "category": "safe", "hidden_source": False, "aliases": []},
    {"food_name": "tomato", "gluten_risk": 0, "category": "safe", "hidden_source": False, "aliases": []},
]

def initialize_gluten_database(db: Session):
    """Initialize gluten database with predefined foods"""
    # Check if database is already populated
    count = db.query(GlutenDatabase).count()
    if count > 0:
        return  # Already initialized
    
    print("🔄 Initializing gluten database...")
    
    for food_data in GLUTEN_DATABASE:
        db_food = GlutenDatabase(**food_data)
        db.add(db_food)
    
    db.commit()
    print(f"✅ Added {len(GLUTEN_DATABASE)} foods to gluten database")

# Initialize Groq client for validation (module-level, shared)
_groq_client = None
if settings.GROQ_API_KEY:
    try:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    except:
        pass

def get_gluten_risk_for_meal(food_names: List[str], db: Session) -> Dict[str, Any]:
    """
    Calculate gluten risk for a meal based on detected foods
    Enhanced with better matching for desi foods
    """
    if not food_names:
        return {
            "gluten_risk_score": 0.0,
            "contains_gluten": False,
            "gluten_sources": []
        }
    
    gluten_risks = []
    gluten_sources = []
    
    # Desi food aliases for better matching
    desi_aliases = {
        "chapati": "roti", "chappati": "roti", "chapathi": "roti", "phulka": "roti",
        "parantha": "paratha", "parota": "paratha",
        "poori": "puri", "bhatura": "bhatura", "bhatoora": "bhatura",
        "samosas": "samosa", "pakoras": "pakora", "kachoris": "kachori",
        "daal": "dal", "lentil": "dal", "lentils": "dal",
        "sabzi": "curry", "sabji": "curry",
        "aloo": "potato", "gobi": "cauliflower", "paneer": "paneer"
    }
    
    for food_name in food_names:
        food_lower = food_name.lower().strip()
        
        # Check aliases first
        if food_lower in desi_aliases:
            food_lower = desi_aliases[food_lower]
        
        # Try exact match first
        food_item = db.query(GlutenDatabase).filter(
            GlutenDatabase.food_name == food_lower
        ).first()
        
        if food_item:
            gluten_risks.append(food_item.gluten_risk)
            if food_item.gluten_risk >= 70:
                gluten_sources.append(food_item.food_name)
        else:
            # Try partial match (check if food name contains or is contained in database entry)
            matched = False
            food_items = db.query(GlutenDatabase).all()
            
            for item in food_items:
                # Check both directions: food in item.food_name OR item.food_name in food
                if (item.food_name in food_lower or food_lower in item.food_name or
                    # Check aliases
                    (item.aliases and any(alias in food_lower for alias in item.aliases if alias))):
                    gluten_risks.append(item.gluten_risk)
                    if item.gluten_risk >= 70:
                        gluten_sources.append(item.food_name)
                    matched = True
                    break
            
            # If still no match, check for common patterns
            if not matched:
                # Check for desi flatbread keywords
                if any(word in food_lower for word in ["roti", "chapati", "naan", "paratha", "puri", "bhatura"]):
                    gluten_risks.append(100)
                    gluten_sources.append(food_lower)
                # Check for bread/wheat keywords
                elif any(word in food_lower for word in ["bread", "wheat", "flour"]):
                    gluten_risks.append(100)
                    gluten_sources.append(food_lower)
                # Check for pasta/noodles
                elif any(word in food_lower for word in ["pasta", "noodle", "spaghetti"]):
                    gluten_risks.append(95)
                    gluten_sources.append(food_lower)
                # Check for fried snacks
                elif any(word in food_lower for word in ["samosa", "pakora", "kachori"]):
                    gluten_risks.append(90)
                    gluten_sources.append(food_lower)
                # Safe foods
                elif any(word in food_lower for word in ["rice", "dal", "egg", "chicken", "fish", "meat", "vegetable", "fruit"]):
                    gluten_risks.append(5)
                else:
                    # Unknown food - default to medium risk
                    gluten_risks.append(30)
    
    # Calculate overall risk (max risk among all foods)
    gluten_risk_score = max(gluten_risks) if gluten_risks else 30.0
    contains_gluten = gluten_risk_score >= 70
    
    # Validate with Groq LLM if available (cross-validation)
    if _groq_client and food_names:
        try:
            validated_risk = _validate_gluten_risk_with_groq(food_names, gluten_risk_score)
            if validated_risk is not None:
                # Use validated risk if significantly different (more than 20 points)
                if abs(validated_risk - gluten_risk_score) > 20:
                    print(f"🔍 Groq risk validation: {gluten_risk_score} → {validated_risk}")
                    gluten_risk_score = validated_risk
                    contains_gluten = gluten_risk_score >= 70
        except Exception as e:
            print(f"⚠️ Groq risk validation failed: {e}")
    
    return {
        "gluten_risk_score": float(gluten_risk_score),
        "contains_gluten": contains_gluten,
        "gluten_sources": gluten_sources if gluten_sources else None
    }

def _validate_gluten_risk_with_groq(food_names: List[str], calculated_risk: float) -> Optional[float]:
    """
    Validate gluten risk score using Groq LLM
    Demonstrates LLM-based validation in NLP pipeline
    """
    if not _groq_client:
        return None
    
    try:
        foods_str = ", ".join(food_names)
        prompt = f"""Analyze these foods and determine gluten risk (0-100):
Foods: {foods_str}
Calculated risk: {calculated_risk}/100

Consider:
- Roti, chapati, naan, paratha, bread, pasta = 100 (wheat flour)
- Samosa, pakora, kachori = 90 (wheat-based pastry)
- Rice, dal, eggs, chicken, vegetables = 5 (gluten-free)
- If ANY food contains gluten, risk should be high

Respond with ONLY a number 0-100, nothing else.
Example: 100 or 5 or 90"""

        response = _groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a gluten risk assessment expert. Analyze foods and return risk score 0-100."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract number
        import re
        numbers = re.findall(r'\d+', content)
        if numbers:
            risk = float(numbers[0])
            if 0 <= risk <= 100:
                return risk
        
        return None
    except Exception as e:
        print(f"⚠️ Groq risk validation error: {e}")
        return None

