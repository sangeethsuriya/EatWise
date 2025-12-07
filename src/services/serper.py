
import os
import httpx
import json
from typing import List, Dict, Any

class SerperService:
    """
    Wrapper for Serper.dev API to perform Google Searches and Places interaction.
    """
    BASE_URL = "https://google.serper.dev"
    
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            print("⚠️ SERPER_API_KEY not found in environment.")
            
    async def search(self, query: str, location: str = "London, UK") -> List[Dict[str, Any]]:
        """General Google Search"""
        if not self.api_key: return []
        
        url = f"{self.BASE_URL}/search"
        payload = json.dumps({
            "q": query,
            "location": location,
            "gl": "gb" # Target UK
        })
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, data=payload)
                data = response.json()
                return data.get("organic", [])
            except Exception as e:
                print(f"Serper Search Error: {e}")
                return []

    async def find_places(self, query: str, location: str = "London") -> List[Dict[str, Any]]:
        """Find places (restaurants, shops)"""
        if not self.api_key: return []
        
        url = f"{self.BASE_URL}/places"
        # Places API expects separate location or embedded in query?
        # Serper places endpoint: {"q": "Restaurants in London"}
        payload = json.dumps({
            "q": f"{query} in {location}",
            "gl": "gb"
        })
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, data=payload)
                data = response.json()
                return data.get("places", [])
            except Exception as e:
                print(f"Serper Places Error: {e}")
                return []
                
    async def shopping_search(self, query: str, location: str = "London") -> List[Dict[str, Any]]:
         """Specific Shopping Search"""
         if not self.api_key: return []
         
         url = f"{self.BASE_URL}/shopping"
         payload = json.dumps({
             "q": query,
             "location": location,
             "gl": "gb"
         })
         headers = {
             'X-API-KEY': self.api_key,
             'Content-Type': 'application/json'
         }
         
         async with httpx.AsyncClient() as client:
             try:
                 response = await client.post(url, headers=headers, data=payload)
                 data = response.json()
                 return data.get("shopping", [])
             except Exception as e:
                 print(f"Serper Shopping Error: {e}")
                 return []
