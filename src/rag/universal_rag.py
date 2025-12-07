
import asyncio
import os
import json
from typing import Optional, Dict

from ..services.serper import SerperService
from .store import NutritionVectorStore
from .dietary_store import DietaryVectorStore
from spoon_ai.chat import ChatBot

class UniversalNutritionRag:
    """
    The Single Source of Truth for Nutrition.
    Aggregates:
    1. Dietary Recommendations (Local Fixed Data)
    2. Cached Learned Knowledge (Vector Store)
    3. Live Web Search (Serper)
    """

    def __init__(self):
        self.dietary_store = DietaryVectorStore() # Specific advice
        self.knowledge_store = NutritionVectorStore(persist_directory="data") # Learned facts
        self.serper = SerperService()
        self.llm = ChatBot(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

    async def search(self, query: str) -> str:
        """
        Main entry point. Returns a natural language answer with sources.
        """
        query = query.lower().strip()

        # 1. Check Dietary Store (High Priority - "How much Vitamin C?")
        dietary_results = self.dietary_store.search(query, top_k=1)
        if dietary_results:
            top_doc = dietary_results[0]
            # If the match is strong or explicitly asking for a nutrient, return it
            # But "Apple" matches "Vitamin C" weakly in some vector stores, so ensure relevance
            if top_doc.get("name", "").lower() in query or query in top_doc.get("name", "").lower():
                return self._format_dietary_response(top_doc)

        # 2. Check Knowledge Store (Learned Facts - "Nutrition of Apple")
        print(f"🔍 Checking Knowledge Cache for: {query}")
        cache_hits = self.knowledge_store.search(query, n_results=1)
        if cache_hits:
            print("✅ Found in Cache!")
            return f"{cache_hits[0]}\n*(Source: Learned Knowledge)*"

        # 3. Web Search (Fallback - "Dragon Fruit specific nutrition")
        print("🌍 Cache Miss. Searching Web...")
        return await self._learn_from_web(query)

    def _format_dietary_response(self, doc: Dict) -> str:
        name = doc.get("name")
        val = doc.get("value")
        # Simply return the fact
        return f"**{name}**: {val}\n*(Source: Official Dietary Guidelines)*"

    async def _learn_from_web(self, query: str) -> str:
        """Search Google, Summarize, Cache."""
        # Search for "query + nutrition facts benefits"
        search_query = f"{query} nutrition facts health benefits"
        
        results = await self.serper.search(search_query)
        if not results:
            return f"I couldn't find information on '{query}'."

        # Aggregate snippets
        context = ""
        for i, res in enumerate(results[:3]):
            context += f"Source {i+1} ({res.get('title')}): {res.get('snippet')}\n"

        # Summarize via LLM
        prompt = f"""
        You are an expert Dietitian. Summarize the following information about "{query}".
        Focus on:
        1. Key Nutrients (Calories, Protein, Vitamins)
        2. Health Benefits
        3. Any dietary warnings
        
        Keep it concise (bullet points).
        
        Sources:
        {context}
        """
        
        response = await self.llm.ask([{"role": "user", "content": prompt}])
        
        # Save to Knowledge Store
        self.knowledge_store.add_knowledge(response, f"learned_{query.replace(' ', '_')}")
        self.knowledge_store.save()
        
        return f"{response}\n*(Learned from Web)*"
