"""
Nutrition Knowledge Store (Simple Keyword Search)

Replaces ChromaDB with a lightweight in-memory store for Python 3.14 compatibility.
"""
import json
import os
from typing import List, Optional, Dict


class NutritionVectorStore:
    """
    Simple in-memory knowledge store using keyword matching.
    Mocking the 'VectorStore' interface for compatibility.
    """
    
    def __init__(self, persist_directory: Optional[str] = "data"):
        """Initialize the store."""
        self.persist_directory = persist_directory
        self.persist_file = os.path.join(persist_directory, "nutrition_store.json") if persist_directory else None
        
        self.documents = []
        self.doc_ids = []
        self.structured_data = {} # Map query -> structured info dict
        
        # Ensure data directory exists
        if self.persist_directory and not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)
            
        # Load existing data if available
        if self.persist_file and os.path.exists(self.persist_file):
            self.load()
        else:
            # Seed with initial knowledge if empty
            self._seed_initial_knowledge()
            if self.persist_file:
                self.save()
    
    def save(self):
        """Save knowledge base to disk."""
        if not self.persist_file:
            return
            
        data = {
            "documents": self.documents,
            "doc_ids": self.doc_ids,
            "structured_data": self.structured_data
        }
        with open(self.persist_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def load(self):
        """Load knowledge base from disk."""
        if not self.persist_file or not os.path.exists(self.persist_file):
            return
            
        try:
            with open(self.persist_file, "r") as f:
                data = json.load(f)
            self.documents = data.get("documents", [])
            self.doc_ids = data.get("doc_ids", [])
            self.structured_data = data.get("structured_data", {})
        except Exception as e:
            print(f"Error loading store: {e}")

    def add_structured_food(self, name: str, info: Dict):
        """Add structured food data for precise direct lookup."""
        self.structured_data[name.lower()] = info
        # Also add a text representation for RAG search
        text_rep = f"Nutrition for {name}: {info.get('description', '')}. "
        for nutrient in info.get('nutrients', []):
             text_rep += f"{nutrient['name']}: {nutrient['amount']}{nutrient['unit']}. "
        self.add_knowledge(text_rep, f"food_{name.lower().replace(' ', '_')}")
        self.save()

    def get_structured_food(self, name: str) -> Optional[Dict]:
        """Direct lookup for a specific food."""
        return self.structured_data.get(name.lower())

    def _seed_initial_knowledge(self):
        """Seed with common nutrition knowledge."""
        knowledge = [
            # Macronutrients
            "Proteins are essential macronutrients that help build and repair muscles. Good sources include chicken, fish, eggs, beans, and tofu. Adults need about 0.8g of protein per kg of body weight daily.",
            "Carbohydrates are the body's main energy source. Complex carbs (whole grains, vegetables) are healthier than simple carbs (sugar, white bread). About 45-65% of daily calories should come from carbs.",
            "Healthy fats are essential for brain function and hormone production. Sources include avocados, nuts, olive oil, and fatty fish. Limit saturated and trans fats.",
            "Fiber aids digestion and helps maintain healthy blood sugar levels. Good sources include whole grains, fruits, vegetables, and legumes. Adults need 25-38g daily.",
            
            # Vitamins
            "Vitamin C boosts immune function and helps absorb iron. Found in citrus fruits, strawberries, bell peppers, and broccoli. Daily need: 65-90mg.",
            "Vitamin D is essential for bone health and immune function. Sources include sunlight, fatty fish, and fortified foods. Many people are deficient.",
            "Vitamin B12 is crucial for nerve function and red blood cell formation. Found mainly in animal products. Vegans should supplement.",
            "Vitamin A supports vision and immune health. Found in carrots, sweet potatoes, spinach, and liver.",
            
            # Minerals
            "Calcium is essential for strong bones and teeth. Found in dairy, leafy greens, and fortified foods. Adults need 1000-1200mg daily.",
            "Iron carries oxygen in the blood. Found in red meat, beans, spinach, and fortified cereals. Women need more iron than men.",
            "Potassium helps regulate blood pressure and muscle function. Found in bananas, potatoes, and leafy greens.",
            "Magnesium supports muscle and nerve function. Found in nuts, seeds, whole grains, and dark chocolate.",
            
            # Dietary Guidelines
            "A balanced diet includes fruits, vegetables, whole grains, lean proteins, and healthy fats. Limit processed foods, added sugars, and sodium.",
            "Hydration is essential. Adults should drink about 8 glasses (2 liters) of water daily, more during exercise or hot weather.",
            "Eating a variety of colorful vegetables ensures you get different nutrients. Each color represents different beneficial compounds.",
            "Portion control is key for weight management. Use smaller plates and be mindful of serving sizes.",
        ]
        
        for i, text in enumerate(knowledge):
            self.add_knowledge(text, f"knowledge_{i}")
    
    def search(self, query: str, n_results: int = 3) -> List[str]:
        """
        Search for relevant nutrition knowledge using finding matching words.
        Simple logic: count overlapping non-stop-words.
        """
        query_words = set(query.lower().split())
        # Remove common stop words (manual list for simplicity)
        stop_words = {"what", "is", "a", "an", "the", "in", "of", "for", "to", "and", "or", "are", "do", "does", "how", "much", "many", "good", "bad", "source", "sources"}
        keywords = query_words - stop_words
        
        if not keywords:
            # If query is only stop words, return random or empty
            return []
            
        scores = []
        for doc in self.documents:
            doc_lower = doc.lower()
            score = 0
            for kw in keywords:
                if kw in doc_lower:
                    score += 1
            scores.append((score, doc))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N results if score > 0
        results = [doc for score, doc in scores[:n_results] if score > 0]
        return results
    
    def add_knowledge(self, text: str, doc_id: Optional[str] = None):
        """Add new knowledge to the store."""
        if doc_id is None:
            doc_id = f"knowledge_{len(self.documents)}"
        
        self.documents.append(text)
        self.doc_ids.append(doc_id)
