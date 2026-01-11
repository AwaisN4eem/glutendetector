"""RAG-powered food search endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()

class FoodSearchResult(BaseModel):
    food_name: str
    gluten_risk: int
    category: str
    description: str
    similarity_score: float

class FoodSearchResponse(BaseModel):
    query: str
    results: List[FoodSearchResult]
    rag_powered: bool = True

@router.get("/search", response_model=FoodSearchResponse)
def search_foods_semantic(
    query: str = Query(..., description="Search query (e.g., 'bread alternatives', 'low gluten foods')"),
    top_k: int = Query(5, description="Number of results", ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    RAG-powered semantic food search
    Uses FAISS vector store + sentence transformers for intelligent food discovery
    """
    try:
        # Build index if not initialized
        if not rag_service.index_initialized:
            rag_service.build_food_index(db)
        
        # Perform semantic search
        results = rag_service.search_foods(query, top_k=top_k)
        
        # Convert to response format
        search_results = [
            FoodSearchResult(
                food_name=r['food_name'],
                gluten_risk=r['gluten_risk'],
                category=r['category'],
                description=r['description'],
                similarity_score=r['similarity_score']
            )
            for r in results
        ]
        
        return FoodSearchResponse(
            query=query,
            results=search_results,
            rag_powered=True
        )
        
    except Exception as e:
        import traceback
        print(f"❌ RAG search error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to search foods: {str(e)}")

@router.get("/alternatives/{food_name}", response_model=FoodSearchResponse)
def get_gluten_free_alternatives(
    food_name: str,
    top_k: int = Query(5, description="Number of alternatives", ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Find gluten-free alternatives to a food using RAG
    Example: 'pizza' → returns 'cauliflower pizza', 'rice-based alternatives'
    """
    try:
        # Build index if not initialized
        if not rag_service.index_initialized:
            rag_service.build_food_index(db)
        
        # Get alternatives
        results = rag_service.get_gluten_free_alternatives(food_name, top_k=top_k)
        
        # Convert to response format
        alternatives = [
            FoodSearchResult(
                food_name=r['food_name'],
                gluten_risk=r['gluten_risk'],
                category=r['category'],
                description=r['description'],
                similarity_score=r['similarity_score']
            )
            for r in results
        ]
        
        return FoodSearchResponse(
            query=f"Gluten-free alternatives to {food_name}",
            results=alternatives,
            rag_powered=True
        )
        
    except Exception as e:
        import traceback
        print(f"❌ RAG alternatives error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to find alternatives: {str(e)}")

@router.get("/similar/{food_name}", response_model=FoodSearchResponse)
def get_similar_foods(
    food_name: str,
    top_k: int = Query(5, description="Number of similar foods", ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Find foods similar to the given food using RAG semantic search
    Example: 'roti' → returns 'chapati', 'naan', 'paratha'
    """
    try:
        # Build index if not initialized
        if not rag_service.index_initialized:
            rag_service.build_food_index(db)
        
        # Search similar foods
        results = rag_service.search_similar_foods(food_name, top_k=top_k)
        
        # Convert to response format
        similar_foods = [
            FoodSearchResult(
                food_name=r['food_name'],
                gluten_risk=r['gluten_risk'],
                category=r['category'],
                description=r['description'],
                similarity_score=r['similarity_score']
            )
            for r in results
        ]
        
        return FoodSearchResponse(
            query=f"Foods similar to {food_name}",
            results=similar_foods,
            rag_powered=True
        )
        
    except Exception as e:
        import traceback
        print(f"❌ RAG similar foods error: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to find similar foods: {str(e)}")


