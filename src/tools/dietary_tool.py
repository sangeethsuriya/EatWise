
from typing import Any
from spoon_ai.tools.base import BaseTool
from ..rag.dietary_store import DietaryVectorStore

class DietaryTool(BaseTool):
    """
    Tool to look up dietary recommendations (Vitamins, Minerals).
    """
    name: str = "dietary_lookup"
    description: str = "Find recommended daily values and benefits for vitamins and minerals."
    
    parameters: dict = {
        "type": "object",
        "properties": {
            "nutrient_name": {
                "type": "string",
                "description": "Name of the vitamin or mineral (e.g., 'Vitamin C', 'Zinc')"
            }
        },
        "required": ["nutrient_name"]
    }
    
    _store: Any = None 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = DietaryVectorStore()
        
    @property
    def store(self):
        return self._store

    def execute(self, nutrient_name: str) -> str:
        """Search for nutrient info."""
        results = self.store.search(nutrient_name)
        if not results:
            return f"I couldn't find specific dietary advice for '{nutrient_name}'."
        
        # Aggregate results
        response = f"**Dietary Recommendations for '{nutrient_name}'**:\n"
        for doc in results[:3]:
            name = doc.get("name")
            val = doc.get("value")
            gender = doc.get("gender")
            age = doc.get("age_group")
            response += f"- **{age} years ({gender})**: {val}\n"
            
        response += "*(Source: UK Government Dietary Recommendations)*"
        return response
