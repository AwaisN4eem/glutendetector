"""RAG (Retrieval Augmented Generation) Service for semantic food search and context retrieval"""
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import json
from models import GlutenDatabase, Meal, Symptom
from sqlalchemy.orm import Session

class RAGService:
    """RAG service using FAISS vector store for semantic search over food database and user history"""
    
    def __init__(self):
        """Initialize RAG service with sentence transformers and FAISS index"""
        print("🔄 Initializing RAG service...")
        
        # Load sentence transformer model for embeddings
        try:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, lightweight model
            print("✅ Sentence transformer model loaded")
        except Exception as e:
            print(f"⚠️ Could not load sentence transformer: {e}")
            self.embedder = None
        
        # FAISS index will be built when needed
        self.food_index = None
        self.food_documents = []
        self.index_initialized = False
    
    def build_food_index(self, db: Session):
        """Build FAISS index from gluten database"""
        if not self.embedder:
            print("⚠️ RAG unavailable - embedder not loaded")
            return
        
        try:
            # Get all foods from database
            foods = db.query(GlutenDatabase).all()
            
            if not foods:
                print("⚠️ No foods in database to index")
                return
            
            # Create documents for each food (name + description + gluten info)
            self.food_documents = []
            texts_to_embed = []
            
            for food in foods:
                doc = {
                    "food_name": food.food_name,
                    "gluten_risk": food.gluten_risk,
                    "category": food.category or "general",
                    "description": food.description or f"{food.food_name} - gluten risk {food.gluten_risk}/100",
                    "hidden_source": food.hidden_source or False,
                    "aliases": food.aliases or []
                }
                self.food_documents.append(doc)
                
                # Create rich text for embedding (includes all searchable info)
                embed_text = f"{food.food_name}. "
                if food.description:
                    embed_text += f"{food.description}. "
                embed_text += f"Gluten risk: {food.gluten_risk}/100. Category: {food.category or 'food'}."
                if food.aliases:
                    aliases_str = ", ".join(food.aliases) if isinstance(food.aliases, list) else str(food.aliases)
                    embed_text += f" Also known as: {aliases_str}."
                
                texts_to_embed.append(embed_text)
            
            # Generate embeddings
            print(f"🔄 Generating embeddings for {len(texts_to_embed)} foods...")
            embeddings = self.embedder.encode(texts_to_embed, show_progress_bar=False)
            embeddings = np.array(embeddings).astype('float32')
            
            # Build FAISS index
            dimension = embeddings.shape[1]
            self.food_index = faiss.IndexFlatL2(dimension)  # L2 distance (cosine similarity alternative)
            self.food_index.add(embeddings)
            
            self.index_initialized = True
            print(f"✅ RAG food index built: {len(self.food_documents)} foods indexed")
            
        except Exception as e:
            print(f"⚠️ Error building RAG index: {e}")
            import traceback
            traceback.print_exc()
    
    def search_foods(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search over food database using RAG"""
        if not self.embedder or not self.index_initialized or not self.food_index:
            return []
        
        try:
            # Embed the query
            query_embedding = self.embedder.encode([query], show_progress_bar=False)
            query_embedding = np.array(query_embedding).astype('float32')
            
            # Search FAISS index
            distances, indices = self.food_index.search(query_embedding, min(top_k, len(self.food_documents)))
            
            # Get results
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.food_documents):
                    doc = self.food_documents[idx].copy()
                    doc['similarity_score'] = float(1 / (1 + distance))  # Convert distance to similarity
                    results.append(doc)
            
            return results
            
        except Exception as e:
            print(f"⚠️ RAG search error: {e}")
            return []
    
    def get_relevant_context_for_question(self, question: str, meals: List[Meal], 
                                          symptoms: List[Symptom], db: Session, 
                                          top_k: int = 3) -> str:
        """
        RAG-enhanced context retrieval for AI Coach
        Retrieves relevant foods from database based on question semantics
        """
        if not self.embedder or not self.index_initialized:
            return ""
        
        try:
            # Search for relevant foods mentioned in question
            relevant_foods = self.search_foods(question, top_k=top_k)
            
            if not relevant_foods:
                return ""
            
            # Build context string from retrieved foods
            context_parts = ["**RAG Retrieved Context (Gluten Database):**"]
            for food in relevant_foods:
                context_parts.append(
                    f"- {food['food_name']}: Risk {food['gluten_risk']}/100, {food['description']}"
                )
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"⚠️ RAG context retrieval error: {e}")
            return ""
    
    def search_similar_foods(self, food_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find foods similar to the given food (useful for substitutions)"""
        return self.search_foods(f"{food_name} similar alternatives", top_k=top_k)
    
    def search_by_category(self, category: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search foods by category using semantic search"""
        return self.search_foods(f"{category} foods", top_k=top_k)
    
    def get_gluten_free_alternatives(self, food_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find gluten-free alternatives to a high-gluten food"""
        results = self.search_foods(f"gluten free alternative to {food_name}", top_k=top_k * 2)
        
        # Filter to only low-gluten foods (risk < 30)
        alternatives = [r for r in results if r['gluten_risk'] < 30]
        
        return alternatives[:top_k]


