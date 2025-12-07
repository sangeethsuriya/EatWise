"""
RAG Tool for SpoonOS

Searches the nutrition knowledge base for relevant information.
"""
from typing import Any
from spoon_ai.tools.base import BaseTool
from ..rag.store import NutritionVectorStore


class RAGTool(BaseTool):
    """Tool to search nutrition knowledge base using RAG."""
    
    name: str = "nutrition_knowledge_search"
    description: str = """Search the nutrition knowledge base for general dietary information.
    Use this tool for questions about vitamins, minerals, dietary guidelines, 
    healthy eating tips, or general nutrition advice (not specific food lookups)."""
    
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The nutrition question or topic to search for"
            }
        },
        "required": ["query"]
    }
    
    _vector_store: NutritionVectorStore = None
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        self._vector_store = NutritionVectorStore()
    
    async def execute(self, query: str) -> str:
        """Search nutrition knowledge and return relevant information."""
        try:
            results = self._vector_store.search(query, n_results=3)
            
            if not results:
                return "No relevant nutrition information found in the knowledge base."
            
            # Format results
            response = "**Nutrition Knowledge:**\n\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. {result}\n\n"
            
            return response
            
        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"
