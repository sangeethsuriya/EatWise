import os
import uuid
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

class VoiceService:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        # Save to src/api/static/audio for frontend access
        self.output_dir = os.path.join(os.getcwd(), "src", "api", "static", "audio")
        os.makedirs(self.output_dir, exist_ok=True)
        
        if not self.api_key:
             print("⚠️ WARNING: ELEVENLABS_API_KEY not found. Voice disabled.")

    async def generate_and_save(self, text: str) -> str | None:
        """Generates audio and saves to static dir. Returns relative web path."""
        if not self.api_key:
            return None

        url = "https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb" # George
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
            if response.status_code != 200:
                print(f"❌ Voice API Error: {response.text}")
                return None
                
            # Save to static/audio file
            filename = f"response_{uuid.uuid4().hex[:8]}.mp3"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            # Return relative path for frontend
            return f"/static/audio/{filename}"
            
        except Exception as e:
            print(f"❌ Voice Generation Error: {e}")
            return None

    async def speak(self, text: str) -> str | None:
        """Async wrapper to generate."""
        return await self.generate_and_save(text)

if __name__ == "__main__":
    svc = VoiceService()
    asyncio.run(svc.speak("Hello! I am your nutrition assistant."))
