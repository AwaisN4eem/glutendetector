"""Meal logging endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import traceback

from database import get_db
from models import Meal, User
from schemas import MealCreate, MealUpdate, MealResponse
from services.nlp_service import NLPService
from services.gluten_db_service import get_gluten_risk_for_meal
from groq import Groq
from config import settings
import re

router = APIRouter()
nlp_service = NLPService()

# Initialize Groq client for detailed descriptions
_groq_client = None
if settings.GROQ_API_KEY:
    try:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        print("✅ Groq client initialized for meal descriptions")
    except Exception as e:
        print(f"⚠️ Could not initialize Groq for meal descriptions: {e}")
else:
    print("⚠️ GROQ_API_KEY not set - detailed meal descriptions will not be generated")

def generate_meal_details_with_groq(description: str, foods: List[str], gluten_risk: float) -> Optional[str]:
    """
    Generate detailed meal description using Groq LLM
    Includes gluten content, serving information, and health insights
    Professional, formatted descriptions for timeline display
    """
    if not _groq_client or not foods:
        return None
    
    try:
        foods_str = ", ".join(foods)
        primary_food = foods[0] if foods else "food"
        
        prompt = f"""You are a nutrition expert analyzing meals for a gluten tracking app.

Meal Description: "{description}"
Detected Foods: {foods_str}
Gluten Risk Score: {gluten_risk}/100

Generate a PROFESSIONAL, DETAILED description (2-3 sentences) that includes:

1. SERVING INFORMATION: Be specific (e.g., "One samosa serving contains approximately 2-3 grams of gluten" or "A typical serving of roti contains 4-5 grams of gluten")

2. GLUTEN SOURCE EXPLANATION: Explain WHY it contains gluten (e.g., "made from wheat flour", "contains wheat-based pastry", "naturally gluten-free")

3. HEALTH IMPLICATION: Brief note about safety (e.g., "This is a high-gluten food that should be avoided by those with celiac disease" or "This is a safe, gluten-free option")

REQUIREMENTS:
- Be specific about serving sizes and gluten amounts in grams
- Use professional, medical terminology when appropriate
- Format clearly with proper grammar
- Keep it concise (2-3 sentences, max 150 words)
- Be accurate and informative

EXAMPLES:

For samosa (90/100):
"One samosa serving contains approximately 2-3 grams of gluten. Samosas are made with wheat flour pastry, which is the primary source of gluten. This is a high-gluten food that should be avoided by those with celiac disease or gluten sensitivity."

For roti/chapati (100/100):
"A typical roti (chapati) serving contains approximately 4-5 grams of gluten. Roti is made from whole wheat flour (atta), which is the primary source of gluten. This is a high-gluten food that should be completely avoided by individuals with celiac disease or gluten sensitivity."

For eggs (5/100):
"Eggs are naturally gluten-free and contain no gluten. This is a safe food option for individuals following a gluten-free diet."

For dal with rice (5/100):
"Dal (lentils) and rice are naturally gluten-free foods. A typical serving contains no gluten, making this a safe meal option for those with celiac disease or gluten sensitivity."

Respond with ONLY the description text, nothing else. No quotes, no formatting, just the plain text description."""

        response = _groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a professional nutritionist and food safety expert providing detailed, accurate food analysis for a medical-grade gluten tracking application."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.2  # Lower temperature for more consistent, professional output
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up formatting
        content = re.sub(r'^["\']|["\']$', '', content)  # Remove quotes
        content = re.sub(r'^\s*["\']|["\']\s*$', '', content)  # Remove quotes with whitespace
        content = content.strip()
        
        # Validate it's not empty and looks like a description
        if content and len(content) > 20:  # Minimum length check
            return content
        else:
            print(f"⚠️ Groq returned invalid description: {content}")
            return None
        
    except Exception as e:
        import traceback
        print(f"⚠️ Groq detail generation error: {e}")
        print(traceback.format_exc())
        return None

@router.post("/", response_model=MealResponse, status_code=201)
def create_meal(
    meal_data: MealCreate,
    user_id: int = Query(1, description="User ID"),
    db: Session = Depends(get_db)
):
    """Log a new meal"""
    
    # Ensure user exists (create default user if needed for MVP)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        try:
            default_user = User(
                id=user_id,
                email=f"user{user_id}@glutenguard.ai",
                username=f"user{user_id}",
                hashed_password="default"  # No auth in MVP
            )
            db.add(default_user)
            db.commit()
            print(f"✅ Created default user {user_id}")
        except Exception as e:
            print(f"⚠️ Could not create user: {e}")
            db.rollback()
    
    try:
        # Extract foods from description using NLP
        try:
            foods_list = nlp_service.extract_food_entities(meal_data.description)
        except Exception as e:
            import traceback
            print(f"⚠️ NLP extraction failed: {e}")
            print(traceback.format_exc())
            # Fallback: use description as food if NLP fails
            foods_list = [meal_data.description.lower()] if meal_data.description else []
        
        # Convert foods list to dict format for response schema
        # NLP returns list of strings, but schema expects list of dicts
        foods_dicts = []
        for food_name in foods_list:
            foods_dicts.append({
                "name": food_name,
                "confidence": 1.0,  # Default confidence for text-based detection
                "gluten_risk": 0  # Will be calculated below
            })
        
        # Calculate gluten risk (using food names)
        try:
            gluten_info = get_gluten_risk_for_meal(foods_list, db)
            # Update gluten risk in food dicts
            for food_dict in foods_dicts:
                food_name = food_dict["name"]
                # Get gluten risk for this specific food
                from services.gluten_db_service import GLUTEN_DATABASE
                from models import GlutenDatabase
                food_item = db.query(GlutenDatabase).filter(
                    GlutenDatabase.food_name == food_name.lower()
                ).first()
                if food_item:
                    food_dict["gluten_risk"] = food_item.gluten_risk
                else:
                    # Try partial match
                    for item in db.query(GlutenDatabase).all():
                        if item.food_name in food_name.lower() or food_name.lower() in item.food_name:
                            food_dict["gluten_risk"] = item.gluten_risk
                            break
                    else:
                        food_dict["gluten_risk"] = 30  # Default
        except Exception as e:
            import traceback
            print(f"⚠️ Gluten risk calculation failed: {e}")
            print(traceback.format_exc())
            # Fallback: default risk
            gluten_info = {
                "gluten_risk_score": 30.0,
                "contains_gluten": False,
                "gluten_sources": None
            }
            for food_dict in foods_dicts:
                food_dict["gluten_risk"] = 30
        
        # Generate detailed description using Groq (for timeline)
        detailed_desc = None
        if foods_list and _groq_client:
            try:
                print(f"🔍 Generating detailed description for: {foods_list} (risk: {gluten_info['gluten_risk_score']})")
                detailed_desc = generate_meal_details_with_groq(meal_data.description, foods_list, gluten_info["gluten_risk_score"])
                if detailed_desc:
                    print(f"✅ Generated description: {detailed_desc[:100]}...")
                else:
                    print("⚠️ Groq returned empty description")
            except Exception as e:
                import traceback
                print(f"⚠️ Groq detail generation failed: {e}")
                print(traceback.format_exc())
        elif not _groq_client:
            print("⚠️ Groq client not available - detailed descriptions disabled")
        
        # Create meal record
        # Store as list of strings in DB (for compatibility)
        # But return as list of dicts in response
        try:
            db_meal = Meal(
                user_id=user_id,
                description=meal_data.description,
                meal_type=meal_data.meal_type,
                timestamp=meal_data.timestamp or datetime.utcnow(),
                input_method=meal_data.input_method or "text",
                raw_text=meal_data.description,
                detected_foods=foods_list,  # Store as list of strings in DB
                gluten_risk_score=gluten_info["gluten_risk_score"],
                contains_gluten=gluten_info["contains_gluten"],
                gluten_sources=gluten_info["gluten_sources"],
                detailed_description=detailed_desc  # Groq-generated detailed description
            )
            
            db.add(db_meal)
            db.commit()
            db.refresh(db_meal)
            
            # Convert detected_foods to dict format for response schema
            # The DB stores as list of strings, but schema expects list of dicts
            if foods_dicts:
                # Create a temporary dict to override the detected_foods
                meal_dict = {
                    "id": db_meal.id,
                    "user_id": db_meal.user_id,
                    "description": db_meal.description,
                    "meal_type": db_meal.meal_type,
                    "timestamp": db_meal.timestamp,
                    "gluten_risk_score": db_meal.gluten_risk_score,
                    "detected_foods": foods_dicts,
                    "contains_gluten": db_meal.contains_gluten,
                    "gluten_sources": db_meal.gluten_sources,
                    "created_at": db_meal.created_at
                }
                return MealResponse(**meal_dict)
            else:
                # If no foods detected, return as-is (schema allows None)
                meal_dict = {
                    "id": db_meal.id,
                    "user_id": db_meal.user_id,
                    "description": db_meal.description,
                    "meal_type": db_meal.meal_type,
                    "timestamp": db_meal.timestamp,
                    "gluten_risk_score": db_meal.gluten_risk_score,
                    "detected_foods": None,
                    "contains_gluten": db_meal.contains_gluten,
                    "gluten_sources": db_meal.gluten_sources,
                    "created_at": db_meal.created_at
                }
                return MealResponse(**meal_dict)
            
            db.add(db_meal)
            db.commit()
            db.refresh(db_meal)
            
            return db_meal
            
        except Exception as e:
            import traceback
            print(f"❌ Database error creating meal: {e}")
            print(traceback.format_exc())
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save meal: {str(e)}")
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        print(f"❌ Unexpected error in create_meal: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to log meal: {str(e)}")

@router.get("/", response_model=List[MealResponse])
def get_meals(
    user_id: int = Query(1, description="User ID"),
    limit: int = Query(50, le=100),
    skip: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get user's meal history"""
    query = db.query(Meal).filter(Meal.user_id == user_id)
    
    if start_date:
        query = query.filter(Meal.timestamp >= start_date)
    if end_date:
        query = query.filter(Meal.timestamp <= end_date)
    
    meals = query.order_by(Meal.timestamp.desc()).offset(skip).limit(limit).all()
    return meals

@router.get("/{meal_id}", response_model=MealResponse)
def get_meal(meal_id: int, db: Session = Depends(get_db)):
    """Get a specific meal"""
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal

@router.put("/{meal_id}", response_model=MealResponse)
def update_meal(
    meal_id: int,
    meal_data: MealUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing meal"""
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    # Get the description to analyze (either new or existing)
    description_to_analyze = meal_data.description if meal_data.description is not None else meal.description
    
    try:
        # Re-analyze if description changed
        if meal_data.description is not None and meal_data.description != meal.description:
            # Extract foods from description using NLP
            try:
                foods_list = nlp_service.extract_food_entities(description_to_analyze)
            except Exception as e:
                import traceback
                print(f"⚠️ NLP extraction failed: {e}")
                print(traceback.format_exc())
                foods_list = [description_to_analyze.lower()] if description_to_analyze else []
            
            # Calculate gluten risk
            try:
                gluten_info = get_gluten_risk_for_meal(foods_list, db)
            except Exception as e:
                import traceback
                print(f"⚠️ Gluten risk calculation failed: {e}")
                print(traceback.format_exc())
                gluten_info = {
                    "gluten_risk_score": meal.gluten_risk_score,
                    "contains_gluten": meal.contains_gluten,
                    "gluten_sources": meal.gluten_sources
                }
            
            # Generate detailed description if foods detected
            detailed_desc = None
            if foods_list and _groq_client:
                try:
                    detailed_desc = generate_meal_details_with_groq(
                        description_to_analyze, 
                        foods_list, 
                        gluten_info["gluten_risk_score"]
                    )
                except Exception as e:
                    print(f"⚠️ Groq detail generation failed: {e}")
            
            # Update meal with new analysis
            meal.description = description_to_analyze
            meal.detected_foods = foods_list
            meal.gluten_risk_score = gluten_info["gluten_risk_score"]
            meal.contains_gluten = gluten_info["contains_gluten"]
            meal.gluten_sources = gluten_info["gluten_sources"]
            meal.raw_text = description_to_analyze
            if detailed_desc:
                meal.detailed_description = detailed_desc
        
        # Update other fields if provided
        if meal_data.meal_type is not None:
            meal.meal_type = meal_data.meal_type
        if meal_data.timestamp is not None:
            meal.timestamp = meal_data.timestamp
        if meal_data.input_method is not None:
            meal.input_method = meal_data.input_method
        
        db.commit()
        db.refresh(meal)
        
        # Convert detected_foods to dict format for response
        foods_dicts = []
        foods_list_for_response = meal.detected_foods if meal.detected_foods else []
        for food_name in foods_list_for_response:
            foods_dicts.append({
                "name": food_name,
                "confidence": 1.0,
                "gluten_risk": 0
            })
        
        # Get gluten risk for each food
        if foods_dicts:
            from services.gluten_db_service import GLUTEN_DATABASE
            from models import GlutenDatabase
            for food_dict in foods_dicts:
                food_item = db.query(GlutenDatabase).filter(
                    GlutenDatabase.food_name == food_dict["name"].lower()
                ).first()
                if food_item:
                    food_dict["gluten_risk"] = food_item.gluten_risk
                else:
                    food_dict["gluten_risk"] = 30
        
        # Create response dict
        meal_dict = {
            "id": meal.id,
            "user_id": meal.user_id,
            "description": meal.description,
            "meal_type": meal.meal_type,
            "timestamp": meal.timestamp,
            "gluten_risk_score": meal.gluten_risk_score,
            "detected_foods": foods_dicts if foods_dicts else None,
            "contains_gluten": meal.contains_gluten,
            "gluten_sources": meal.gluten_sources,
            "created_at": meal.created_at
        }
        
        return MealResponse(**meal_dict)
        
    except Exception as e:
        import traceback
        print(f"❌ Error updating meal: {e}")
        print(traceback.format_exc())
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update meal: {str(e)}")

@router.delete("/{meal_id}", status_code=204)
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    """Delete a meal"""
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    db.delete(meal)
    db.commit()
    return None

@router.post("/generate-descriptions", status_code=200)
def generate_descriptions_for_existing_meals(
    user_id: int = Query(1, description="User ID"),
    limit: int = Query(50, description="Number of meals to process"),
    db: Session = Depends(get_db)
):
    """Generate detailed descriptions for existing meals that don't have them"""
    if not _groq_client:
        raise HTTPException(status_code=400, detail="Groq API key not set. Cannot generate descriptions.")
    
    # Get meals without detailed descriptions
    meals = db.query(Meal).filter(
        Meal.user_id == user_id,
        (Meal.detailed_description == None) | (Meal.detailed_description == "")
    ).limit(limit).all()
    
    if not meals:
        return {"message": "All meals already have descriptions", "processed": 0}
    
    processed = 0
    failed = 0
    
    for meal in meals:
        try:
            # Get detected foods
            foods_list = meal.detected_foods if meal.detected_foods else []
            if not foods_list and meal.description:
                # Try to extract foods from description
                foods_list = nlp_service.extract_food_entities(meal.description)
            
            if foods_list:
                # Generate description
                detailed_desc = generate_meal_details_with_groq(
                    meal.description, 
                    foods_list, 
                    meal.gluten_risk_score
                )
                
                if detailed_desc:
                    meal.detailed_description = detailed_desc
                    processed += 1
                else:
                    failed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"⚠️ Failed to generate description for meal {meal.id}: {e}")
            failed += 1
    
    db.commit()
    
    return {
        "message": f"Generated descriptions for {processed} meals",
        "processed": processed,
        "failed": failed,
        "total": len(meals)
    }

