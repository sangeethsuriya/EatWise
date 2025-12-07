
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.graph.workflow import create_nutrition_graph
from src.memory.user_profile import UserProfileStore
from src.db.database import engine
from src.db import models
from src.api.auth import router as auth_router
from src.api.graph import router as graph_router

# Init DB
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nutrition Dietitian API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(graph_router)

# Initialize Graph & Memory
try:
    graph_app = create_nutrition_graph()
    memory_store = UserProfileStore()
    print("✅ Graph and Memory initialized.")
except Exception as e:
    print(f"❌ Failed to init components: {e}")
    graph_app = None

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Models
class ChatRequest(BaseModel):
    query: str
    voice_enabled: bool = False
    session_id: Optional[str] = None # New Field

class ChatResponse(BaseModel):
    response_text: str
    audio_path: Optional[str] = None
    intent: Optional[str] = None
    session_id: Optional[str] = None

class SessionCreate(BaseModel):
    title: str = "New Chat"

class HistoryItem(BaseModel):
    date: str
    food: str
    nutrients: dict

# Endpoints

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "landing.html"))

@app.get("/onboarding")
async def onboarding_page():
    return FileResponse(os.path.join(static_dir, "onboarding.html"))

@app.get("/dashboard")
async def dashboard_page():
    return FileResponse(os.path.join(static_dir, "dashboard.html"))

# --- Session Endpoints ---
@app.get("/sessions")
async def get_sessions():
    """Get list of past sessions."""
    return memory_store.get_all_sessions()

@app.post("/sessions")
async def create_session(session: SessionCreate):
    """Create new session."""
    sid = memory_store.create_session(session.title)
    return {"id": sid, "title": session.title}

@app.get("/sessions/{session_id}")
async def get_session_messages(session_id: str):
    """Get messages for a session."""
    msgs = memory_store.get_session_messages(session_id)
    return msgs

# --- Chat Endpoint ---
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not graph_app:
        raise HTTPException(status_code=500, detail="Graph not initialized")
    
    # 1. Ensure Session ID
    sid = request.session_id
    if not sid:
        sid = memory_store.create_session(title=request.query[:30]) # Auto-title
    
    # 2. Log User Message
    memory_store.add_message(sid, "user", request.query)
    
    # 3. Extract Facts (Simple Heuristic for now)
    if "i am" in request.query.lower():
         memory_store.save_fact(request.query)

    try:
        inputs = {
            "query": request.query,
            "voice_enabled": request.voice_enabled
        }
        result = await graph_app.invoke(inputs)
        
        response_text = result.get("response_text", "")
        
        # 4. Log Bot Message
        memory_store.add_message(sid, "assistant", response_text)
        
        return ChatResponse(
            response_text=response_text,
            audio_path=result.get("audio_path"),
            intent=result.get("intent"),
            session_id=sid
        )
    except Exception as e:
        print(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history", response_model=List[HistoryItem])
async def get_history():
    try:
        today_logs = memory_store.get_today_log()
        return today_logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/favorites")
async def get_favorites():
    return {"favorites": memory_store.get_favorites()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
