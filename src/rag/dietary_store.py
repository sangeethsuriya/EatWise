
import json
import os
import numpy as np
from typing import List, Dict, Any

class DietaryVectorStore:
    """
    Simple Vector Store for Dietary Recommendations.
    Loads JSONs and performs keyword/similarity search.
    """
    def __init__(self, data_dir: str = "data/recommendations"):
        self.data_dir = data_dir
        self.documents = []
        self._load_data()

    def _load_data(self):
        """Load all JSON files from the data directory."""
        if not os.path.exists(self.data_dir):
            return

        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        # Handle new complex structure (Age -> Gender -> Nutrients)
                        if isinstance(data, dict):
                            # Flatten for search index
                            for age_group, genders in data.items():
                                for gender, nutrients in genders.items():
                                    if isinstance(nutrients, dict):
                                        for nutrient, value in nutrients.items():
                                            # Clean name: vitamin_c_mg -> Vitamin C
                                            pretty_name = nutrient.replace("_", " ").title()
                                            for suffix in [" Mg", " Mcg", " G", " Iu"]:
                                                if pretty_name.endswith(suffix):
                                                    pretty_name = pretty_name[:-len(suffix)]
                                            
                                            doc = {
                                                "name": pretty_name.strip(),
                                                "value": value, 
                                                "age_group": age_group,
                                                "gender": gender,
                                                "source_file": filename
                                            }
                                            self.documents.append(doc)
                        elif isinstance(data, list):
                            self.documents.extend(data)
                            
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find best matching recommendation.
        Returns multiple results to cover age/gender context.
        """
        query = query.lower()
        results = []
        
        # Tokenize query
        query_tokens = set(query.split())
        
        for doc in self.documents:
            score = 0
            name = doc.get("name", "").lower() # e.g. "vitamin c"
            name_tokens = set(name.split())
            
            # 1. Exact Name match in query
            if name in query:
                score += 20
                
            # 2. Strong token overlap (Vitamin + C)
            intersection = query_tokens.intersection(name_tokens)
            if len(intersection) >= 2: # "vitamin" + "c"
                score += 10
            elif "vitamin" not in name and len(intersection) >= 1: # "zinc", "iron" (single word)
                 # avoid matching "vitamin" alone for "vitamin a" query matching "vitamin c" doc
                 score += 10
            
            # Boost if query mentions gender/age
            if doc.get("gender", "") in query:
                score += 5
            
            if score > 0:
                results.append((score, doc))
        
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:top_k]]
