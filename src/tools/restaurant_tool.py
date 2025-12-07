
from typing import Any
from spoon_ai.tools.base import BaseTool
from ..services.serper import SerperService
import asyncio

class RestaurantTool(BaseTool):
    name: str = "restaurant_search"
    description: str = "Find restaurants and dining options near a location."
    parameters: dict = {
        "type": "object",
        "properties": {
            "cuisine_query": {
                "type": "string",
                "description": "Cuisine or type (e.g. 'Italian', 'Vegan', 'Nice dinner')"
            },
            "location": {
                "type": "string",
                "description": "User's location (default: London)"
            }
        },
        "required": ["cuisine_query"]
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = SerperService()

    async def execute(self, cuisine_query: str, location: str = "London") -> str:
        """Find restaurants."""
        places = await self._service.find_places(cuisine_query, location)
        
        if not places:
            return f"I couldn't find any restaurants matching '{cuisine_query}' in {location}."

        response = f"**Restaurant Recommendations for {cuisine_query} ({location}):**\n"
        for place in places[:4]:
            name = place.get("title", "Unknown")
            rating = place.get("rating", "N/A")
            address = place.get("address", "No address")
            response += f"- **{name}** (⭐{rating}): {address}\n"
            
        return response
