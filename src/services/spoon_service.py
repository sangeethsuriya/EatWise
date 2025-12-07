
from spoon_ai.llm import LLMManager, OpenAIProvider
import os
from dotenv import load_dotenv

load_dotenv()

class SpoonService:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Initialize OpenAI Provider directly
        # It typically reads from env
        self.provider = OpenAIProvider()
        print("🥄 SpoonOS LLM Service Initialized (Direct Provider)")

    async def chat(self, messages: list, model: str = "gpt-4o-mini") -> str:
        try:
            # Attempt unified 'chat' method
            if hasattr(self.provider, 'chat'):
                response = await self.provider.chat(messages=messages, model=model)
            else:
                # Fallback to 'generate_response' or similar if 'chat' fails
                response = await self.provider.generate_response(messages=messages, model=model)
            
            # Extract content if object
            if hasattr(response, 'content'):
                return response.content
            if isinstance(response, dict) and 'content' in response:
                return response['content']
            return str(response)
            
        except Exception as e:
            print(f"Spoon LLM Error: {e}")
            raise e
