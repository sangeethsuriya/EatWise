
from typing import Dict, TypedDict, Any
from spoon_ai.graph import StateGraph, START, END
# Updated Tools
from src.rag.universal_rag import UniversalNutritionRag
from src.tools.shopping_tool import ShoppingTool
from src.tools.restaurant_tool import RestaurantTool
from src.memory.user_profile import UserProfileStore
from src.services.voice import VoiceService
# Spoon Service
from src.services.spoon_service import SpoonService

import os
import asyncio
import json

# Define State
class NutritionState(TypedDict):
    query: str
    response_text: str
    audio_path: str | None
    error: str | None
    intent: str | None # ASK, SHOP, EAT, LOG
    voice_enabled: bool # Toggle for voice output

# Define Nodes
class NutritionGraphNodes:
    def __init__(self):
        # Universal RAG replaces Smart/Dietary tools
        self.rag = UniversalNutritionRag()
        self.shop_tool = ShoppingTool()
        self.eat_tool = RestaurantTool()
        self.memory = UserProfileStore()
        self.voice = VoiceService()
        self.spoon = SpoonService.get_instance() # Singleton
        
    async def route_query(self, state: NutritionState) -> Dict[str, Any]:
        """Node 0: Router - Decide intent"""
        query = state["query"]
        
        prompt = f"""
        Classify this query: "{query}"
        Output ONLY one word:
        - "LOG" if user says they ate something (e.g. "I ate an apple", "Add burger").
        - "SHOP" if user wants to buy food (e.g. "Buy noodles", "Tesco nearby").
        - "EAT" if user wants restaurant (e.g. "Suggest dinner", "Vegan restaurants").
        - "ASK" if asking questions (e.g. "Apple calories", "Is Keto good?").
        - "CHAT" for greetings.
        """
        response = await self.spoon.chat([{"role": "user", "content": prompt}], model="gpt-4o-mini")
        intent = response.strip().upper()
        
        # Cleanup
        valid_intents = ["LOG", "SHOP", "EAT", "ASK"]
        if any(v in intent for v in valid_intents):
            for v in valid_intents:
                if v in intent:
                    return {"intent": v}
        return {"intent": "ASK"} # Default fallback

    async def process_log(self, state: NutritionState) -> Dict[str, Any]:
        """Node: Log Food"""
        query = state["query"]
        prompt = f"Extract the food name from: '{query}'. Output ONLY the name."
        food_name = await self.spoon.chat([{"role": "user", "content": prompt}])
        food_name = food_name.strip()
        
        self.memory.log_food(food_name, {"source": "user_input"})
        return {"response_text": f"Tracking: I've logged **{food_name}** to your daily intake."}

    async def process_shop(self, state: NutritionState) -> Dict[str, Any]:
        """Node: Shopping"""
        prompt = f"Extract the product to buy from: '{state['query']}'. Output ONLY the product name."
        product = await self.spoon.chat([{"role": "user", "content": prompt}])
        
        response = await self.shop_tool.execute(product.strip())
        return {"response_text": response}

    async def process_eat(self, state: NutritionState) -> Dict[str, Any]:
        """Node: Restaurant"""
        prompt = f"Extract the cuisine or restaurant type from: '{state['query']}'. Output ONLY the type."
        cuisine = await self.spoon.chat([{"role": "user", "content": prompt}])
        
        response = await self.eat_tool.execute(cuisine.strip())
        return {"response_text": response}

    async def process_ask(self, state: NutritionState) -> Dict[str, Any]:
        """Node: Universal RAG (Facts + Advice)"""
        try:
            # 1. Get Raw Fact (Optimize latency here if possible)
            raw_data = await self.rag.search(state["query"])
            
            # 2. Humanize
            prompt = f"""
            You are EatWise, a sophisticated, highly knowledgeable clinical nutritionist.
            
            User Query: "{state['query']}"
            Found Information: "{raw_data}"
            
            Task: Synthesize a helpful, warm response. 
            - Use short paragraphs and markdown.
            - Be encouraging but scientific.
            """
            
            response = await self.spoon.chat([{"role": "user", "content": prompt}])
            return {"response_text": response}
            
        except Exception as e:
            return {"response_text": "I apologize, but I'm having trouble retrieving that information right now. Could you rephrase?", "error": str(e)}

    async def generate_voice(self, state: NutritionState) -> Dict[str, Any]:
        """Node: Voice"""
        if not state.get("voice_enabled", False):
            return {"audio_path": None}

        text = state.get("response_text", "")
        if not text: return {}
        
        # Increased limit for voice
        clean_text = text.replace("**", "").replace("*", "")
        if len(clean_text) > 1000:
            clean_text = clean_text[:1000] + "..."
            
        try:
            audio_path = await self.voice.speak(clean_text)
            return {"audio_path": audio_path}
        except Exception as e:
            return {"error": f"Voice failed: {e}"}

# Build Graph
def create_nutrition_graph():
    nodes = NutritionGraphNodes()
    workflow = StateGraph(NutritionState)
    
    # Nodes
    workflow.add_node("router", nodes.route_query)
    workflow.add_node("process_log", nodes.process_log)
    workflow.add_node("process_shop", nodes.process_shop)
    workflow.add_node("process_eat", nodes.process_eat)
    workflow.add_node("process_ask", nodes.process_ask)
    workflow.add_node("generate_voice", nodes.generate_voice)
    
    # Edges
    workflow.set_entry_point("router")
    
    def route_decision(state):
        intent = state.get('intent', 'ASK').lower()
        if intent == 'chat': intent = 'ask' 
        return f"process_{intent}"
    
    destinations = {
        "process_log": "process_log",
        "process_shop": "process_shop",
        "process_eat": "process_eat",
        "process_ask": "process_ask"
    }
    
    workflow.add_conditional_edges("router", route_decision, destinations)
    
    for node in destinations.values():
        workflow.add_edge(node, "generate_voice")
        
    workflow.add_edge("generate_voice", END)
    
    return workflow.compile()
