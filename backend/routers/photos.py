"""Food photo upload and detection endpoints"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from datetime import datetime

from database import get_db
from models import FoodPhoto, Meal
from schemas import FoodPhotoResponse, MealResponse
from services.cv_service import CVService
from services.gluten_db_service import get_gluten_risk_for_meal
from config import settings

router = APIRouter()
cv_service = CVService()

@router.post("/upload", response_model=FoodPhotoResponse, status_code=201)
async def upload_food_photo(
    file: UploadFile = File(...),
    user_id: int = Query(1, description="User ID"),
    create_meal: bool = Query(True, description="Auto-create meal from photo"),
    db: Session = Depends(get_db)
):
    """Upload and analyze a food photo"""
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Ensure uploads directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Generate filename using original filename (sanitized) with timestamp for uniqueness
        import re
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        
        # Get original filename without extension
        original_name = os.path.splitext(file.filename)[0] if file.filename else "image"
        # Sanitize filename (remove special characters, keep alphanumeric, underscore, hyphen)
        sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '_', original_name)
        # Limit length
        sanitized_name = sanitized_name[:50] if len(sanitized_name) > 50 else sanitized_name
        
        # Add timestamp for uniqueness while keeping original name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{sanitized_name}.{file_extension}"
        filepath = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Save file
        try:
            content = await file.read()
            file_size = len(content)
            
            # Check file size before saving
            if file_size > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB)")
            
            if file_size == 0:
                raise HTTPException(status_code=400, detail="File is empty")
            
            with open(filepath, "wb") as f:
                f.write(content)
        except OSError as e:
            import traceback
            print(f"❌ Error saving file: {e}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Process image with CV service
        try:
            start_time = datetime.utcnow()
            detection_result = cv_service.detect_food(filepath)
            processing_time = (datetime.utcnow() - start_time).total_seconds()
        except Exception as e:
            import traceback
            print(f"❌ Error processing image: {e}")
            print(traceback.format_exc())
            # Clean up uploaded file if processing fails
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")
    
        # Create photo record
        try:
            db_photo = FoodPhoto(
                user_id=user_id,
                filename=unique_filename,
                filepath=filepath,
                file_size=file_size,
                detected_foods=detection_result["detected_foods"],
                primary_food=detection_result["primary_food"],
                gluten_risk_score=detection_result["gluten_risk_score"],
                processing_time=processing_time,
                processed=True
            )
            
            db.add(db_photo)
            db.commit()
            db.refresh(db_photo)
            
            # Auto-create meal if requested
            if create_meal and detection_result["detected_foods"]:
                food_names = [f["name"] for f in detection_result["detected_foods"]]
                description = f"Photo meal: {', '.join(food_names)}"
                
                # Calculate gluten info
                gluten_info = get_gluten_risk_for_meal(food_names, db)
                
                db_meal = Meal(
                    user_id=user_id,
                    description=description,
                    meal_type="photo",
                    timestamp=datetime.utcnow(),
                    input_method="photo",
                    raw_text=description,
                    detected_foods=detection_result["detected_foods"],
                    gluten_risk_score=gluten_info["gluten_risk_score"],
                    contains_gluten=gluten_info["contains_gluten"],
                    gluten_sources=gluten_info["gluten_sources"]
                )
                
                db.add(db_meal)
                db.commit()
                db.refresh(db_meal)
                
                # Link photo to meal
                db_photo.meal_id = db_meal.id
                db.commit()
            
            return db_photo
            
        except Exception as e:
            import traceback
            print(f"❌ Database error: {e}")
            print(traceback.format_exc())
            # Clean up uploaded file if database operation fails
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to save photo record: {str(e)}")
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        print(f"❌ Unexpected error in upload_food_photo: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/", response_model=List[FoodPhotoResponse])
def get_photos(
    user_id: int = Query(1, description="User ID"),
    limit: int = Query(20, le=50),
    skip: int = 0,
    db: Session = Depends(get_db)
):
    """Get user's food photos"""
    photos = db.query(FoodPhoto).filter(
        FoodPhoto.user_id == user_id
    ).order_by(FoodPhoto.uploaded_at.desc()).offset(skip).limit(limit).all()
    
    return photos

@router.get("/{photo_id}", response_model=FoodPhotoResponse)
def get_photo(photo_id: int, db: Session = Depends(get_db)):
    """Get a specific photo"""
    photo = db.query(FoodPhoto).filter(FoodPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo

@router.delete("/{photo_id}", status_code=204)
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    """Delete a photo"""
    photo = db.query(FoodPhoto).filter(FoodPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Delete file
    if os.path.exists(photo.filepath):
        os.remove(photo.filepath)
    
    db.delete(photo)
    db.commit()
    return None

