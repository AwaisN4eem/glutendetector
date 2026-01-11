"""Generate sample data for demo purposes"""
import random
import bcrypt
from datetime import datetime, timedelta
from database import SessionLocal, init_db
from models import User, Meal, Symptom


def hash_password(password: str) -> str:
    """Hash password using bcrypt directly"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Sample meals with varying gluten content
SAMPLE_MEALS = [
    # High gluten meals (70-100)
    {"description": "Had a sandwich with wheat bread, turkey, and cheese", "gluten_risk": 95, "contains_gluten": True, "gluten_sources": ["bread", "wheat bread"]},
    {"description": "Ate spaghetti with marinara sauce for dinner", "gluten_risk": 100, "contains_gluten": True, "gluten_sources": ["pasta", "spaghetti"]},
    {"description": "Pizza with pepperoni and mushrooms", "gluten_risk": 100, "contains_gluten": True, "gluten_sources": ["pizza"]},
    {"description": "Bagel with cream cheese and coffee", "gluten_risk": 100, "contains_gluten": True, "gluten_sources": ["bagel"]},
    {"description": "Pancakes with syrup and butter for breakfast", "gluten_risk": 95, "contains_gluten": True, "gluten_sources": ["pancakes"]},
    {"description": "Beer and pretzels at happy hour", "gluten_risk": 100, "contains_gluten": True, "gluten_sources": ["beer", "pretzel"]},
    {"description": "Chicken sandwich with french fries", "gluten_risk": 90, "contains_gluten": True, "gluten_sources": ["bread", "sandwich"]},
    {"description": "Ramen noodles with vegetables", "gluten_risk": 95, "contains_gluten": True, "gluten_sources": ["noodles", "ramen"]},
    
    # Medium gluten meals (30-69)
    {"description": "Oatmeal with banana and honey", "gluten_risk": 50, "contains_gluten": False, "gluten_sources": None},
    {"description": "Fried chicken with coleslaw", "gluten_risk": 60, "contains_gluten": True, "gluten_sources": ["breaded"]},
    {"description": "Soup with crackers", "gluten_risk": 70, "contains_gluten": True, "gluten_sources": ["crackers"]},
    
    # Low gluten meals (0-29)
    {"description": "Grilled chicken with rice and broccoli", "gluten_risk": 10, "contains_gluten": False, "gluten_sources": None},
    {"description": "Salad with grilled salmon and olive oil dressing", "gluten_risk": 10, "contains_gluten": False, "gluten_sources": None},
    {"description": "Scrambled eggs with bacon and fruit", "gluten_risk": 5, "contains_gluten": False, "gluten_sources": None},
    {"description": "Corn tacos with beef, lettuce, and salsa", "gluten_risk": 10, "contains_gluten": False, "gluten_sources": None},
    {"description": "Quinoa bowl with vegetables and avocado", "gluten_risk": 5, "contains_gluten": False, "gluten_sources": None},
    {"description": "Baked salmon with sweet potato and asparagus", "gluten_risk": 10, "contains_gluten": False, "gluten_sources": None},
    {"description": "Greek yogurt with berries and nuts", "gluten_risk": 15, "contains_gluten": False, "gluten_sources": None},
    {"description": "Stir-fry with rice, chicken, and vegetables", "gluten_risk": 10, "contains_gluten": False, "gluten_sources": None},
]

# Sample symptoms that correlate with gluten
SAMPLE_SYMPTOMS = [
    {"description": "Feeling bloated and uncomfortable", "severity": 6, "symptom_type": "bloating"},
    {"description": "Terrible bloating and gas", "severity": 8, "symptom_type": "bloating"},
    {"description": "Stomach pain after eating", "severity": 7, "symptom_type": "pain"},
    {"description": "Severe abdominal cramping", "severity": 9, "symptom_type": "pain"},
    {"description": "Feeling nauseous and queasy", "severity": 5, "symptom_type": "nausea"},
    {"description": "Extreme fatigue and brain fog", "severity": 7, "symptom_type": "fatigue"},
    {"description": "Headache and feeling tired", "severity": 6, "symptom_type": "headache"},
    {"description": "Diarrhea after lunch", "severity": 8, "symptom_type": "diarrhea"},
    {"description": "Constipated and uncomfortable", "severity": 5, "symptom_type": "constipation"},
    {"description": "Anxious and irritable mood", "severity": 6, "symptom_type": "mood"},
]

MILD_SYMPTOMS = [
    {"description": "Slight stomach discomfort", "severity": 3, "symptom_type": "pain"},
    {"description": "Mildly tired", "severity": 4, "symptom_type": "fatigue"},
    {"description": "A bit bloated", "severity": 3, "symptom_type": "bloating"},
]

def create_demo_user(db):
    """Create a demo user"""
    user = db.query(User).filter(User.email == "demo@glutenguard.ai").first()
    if user:
        print("Demo user already exists")
        return user
    
    user = User(
        email="demo@glutenguard.ai",
        username="demo",
        hashed_password=hash_password("demo123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✅ Created demo user: {user.email}")
    return user

def generate_sample_data(days=42, end_date: datetime | None = None):
    """
    Generate realistic sample data showing gluten intolerance pattern
    
    Pattern: High gluten meals → symptoms 2-4 hours later
            Low gluten meals → few/no symptoms
    """
    end_date = end_date or datetime.now()
    print(f"🔄 Generating {days} days of sample data ending {end_date.date()} ...")
    
    init_db()
    db = SessionLocal()
    
    try:
        # Create demo user
        user = create_demo_user(db)
        
        # Clear existing data for demo user
        db.query(Meal).filter(Meal.user_id == user.id).delete()
        db.query(Symptom).filter(Symptom.user_id == user.id).delete()
        db.commit()
        
        start_date = end_date - timedelta(days=days)
        meal_count = 0
        symptom_count = 0
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # 3-4 meals per day
            meals_today = random.randint(3, 4)
            meal_times = [8, 12, 18, 21]  # breakfast, lunch, dinner, snack
            meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
            
            for i in range(meals_today):
                hour = meal_times[i]
                meal_time = current_date.replace(hour=hour, minute=random.randint(0, 30))
                
                # 60% chance of high gluten meal (to simulate undiagnosed intolerance)
                if random.random() < 0.6:
                    meal_data = random.choice([m for m in SAMPLE_MEALS if m["gluten_risk"] >= 70])
                else:
                    meal_data = random.choice([m for m in SAMPLE_MEALS if m["gluten_risk"] < 30])
                
                meal = Meal(
                    user_id=user.id,
                    description=meal_data["description"],
                    meal_type=meal_types[i],
                    timestamp=meal_time,
                    gluten_risk_score=meal_data["gluten_risk"],
                    contains_gluten=meal_data["contains_gluten"],
                    gluten_sources=meal_data["gluten_sources"],
                    detected_foods=meal_data["description"].split(),
                    input_method="text"
                )
                db.add(meal)
                meal_count += 1
                
                # If high gluten meal, likely to cause symptoms 2-4 hours later
                if meal_data["gluten_risk"] >= 70:
                    if random.random() < 0.75:  # 75% chance of symptoms after gluten
                        symptom_delay = random.randint(2, 4)
                        symptom_time = meal_time + timedelta(hours=symptom_delay, minutes=random.randint(0, 30))
                        
                        symptom_data = random.choice(SAMPLE_SYMPTOMS)
                        symptom = Symptom(
                            user_id=user.id,
                            description=symptom_data["description"],
                            severity=symptom_data["severity"],
                            symptom_type=symptom_data["symptom_type"],
                            timestamp=symptom_time,
                            time_context=f"{symptom_delay} hours after eating",
                            input_method="text",
                            sentiment_score=-0.7,
                            extracted_symptoms=[{"type": symptom_data["symptom_type"], "mention": symptom_data["symptom_type"]}]
                        )
                        db.add(symptom)
                        symptom_count += 1
                
                # Low gluten meals rarely cause symptoms
                elif meal_data["gluten_risk"] < 30:
                    if random.random() < 0.15:  # Only 15% chance of mild symptoms
                        symptom_delay = random.randint(1, 3)
                        symptom_time = meal_time + timedelta(hours=symptom_delay)
                        
                        symptom_data = random.choice(MILD_SYMPTOMS)
                        symptom = Symptom(
                            user_id=user.id,
                            description=symptom_data["description"],
                            severity=symptom_data["severity"],
                            symptom_type=symptom_data["symptom_type"],
                            timestamp=symptom_time,
                            input_method="text",
                            sentiment_score=-0.3,
                            extracted_symptoms=[{"type": symptom_data["symptom_type"], "mention": symptom_data["symptom_type"]}]
                        )
                        db.add(symptom)
                        symptom_count += 1
        
        db.commit()
        print(f"✅ Generated {meal_count} meals and {symptom_count} symptoms")
        print(f"📊 Date range: {start_date.date()} → {end_date.date()}")
        print(f"📊 This data shows a clear correlation pattern for demo purposes")
        print(f"🌾 User: demo@glutenguard.ai / Password: demo123")
        
    except Exception as e:
        print(f"❌ Error generating data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    
    # Optional second arg: end date in YYYY-MM-DD (e.g., 2026-01-10)
    end_date_arg = sys.argv[2] if len(sys.argv) > 2 else None
    end_date = None
    if end_date_arg:
        try:
            end_date = datetime.strptime(end_date_arg, "%Y-%m-%d")
        except ValueError:
            print(f"⚠️ Invalid date format '{end_date_arg}'. Use YYYY-MM-DD. Falling back to today.")
    
    generate_sample_data(days, end_date)

