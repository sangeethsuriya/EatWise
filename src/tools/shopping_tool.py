
from typing import Any
from spoon_ai.tools.base import BaseTool
from ..services.serper import SerperService
import asyncio

class ShoppingTool(BaseTool):
    name: str = "grocery_search"
    description: str = "Search for grocery products at nearby supermarkets (Tesco, Sainsbury's, etc)."
    parameters: dict = {
        "type": "object",
        "properties": {
            "product_query": {
                "type": "string",
                "description": "What to buy (e.g. 'Instant Noodles', 'Vegan Cheese')"
            },
            "location": {
                "type": "string",
                "description": "User's location (default: London)"
            }
        },
        "required": ["product_query"]
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._service = SerperService() # Private attr

    async def execute(self, product_query: str, location: str = "London") -> str:
        """Find products."""
        # We want to check major chains
        chains = ["Tesco", "Sainsbury's", "Aldi", "Lidl"]
        results = []
        
        # We can do parallel searches or one broad shopping search
        # Broad shopping search is cheaper/faster.
        # "Instant Noodles Tesco London"
        
        # Let's try searching for the product generally first
        items = await self._service.shopping_search(product_query, location)
        
        if not items:
             # Fallback to organic search
             search_q = f"Buy {product_query} supermarkets {location}"
             organic = await self._service.search(search_q, location)
             return self._format_organic(organic)

        return self._format_shopping(items)

    def _format_shopping(self, items: list) -> str:
        if not items:
            return "No specific products found nearby."
        
        response = "**Grocery Suggestions:**\n"
        for item in items[:4]:
            title = item.get("title", "Unknown")
            price = item.get("price", "N/A")
            source = item.get("source", "Unknown Store")
            response += f"- {title} ({price}) @ {source}\n"
        return response

    def _format_organic(self, items: list) -> str:
        if not items:
            return "I couldn't find specific grocery stock info."
            
        response = "**Grocery Search Results:**\n"
        for item in items[:3]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            response += f"- **{title}**: {snippet}\n"
        return response
