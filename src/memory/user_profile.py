
import json
import os
from datetime import datetime, date
from typing import List, Dict, Any

class UserProfileStore:
    """
    Manages user profile, history, and preferences.
    Persists data to specific JSON file.
    """
    def __init__(self, data_file: str = "data/user_profile.json"):
        self.data_file = data_file
        self._ensure_data_dir()
        self.profile = self._load_profile()

    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

    def _load_profile(self) -> Dict[str, Any]:
        if not os.path.exists(self.data_file):
            return {
                "name": "User",
                "favorites": [],
                "history": [], # List of {date, food, nutrients}
                "preferences": [] # e.g. "Vegetarian", "No Nuts"
            }
        try:
            with open(self.data_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading profile: {e}")
            return {"name": "User", "favorites": [], "history": [], "preferences": []}

    def _save_profile(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.profile, f, indent=2)
        except Exception as e:
            print(f"Error saving profile: {e}")

    def log_food(self, food_name: str, nutrients: Dict[str, Any]):
        """Log a food item eaten today."""
        entry = {
            "date": date.today().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "food": food_name,
            "nutrients": nutrients
        }
        self.profile["history"].append(entry)
        
        # Auto-add to favorites if eaten > 3 times? 
        # For now, just manual favorites.
        self._save_profile()

    def add_favorite(self, food_name: str):
        """Add item to favorites if not exists."""
        if food_name not in self.profile["favorites"]:
            self.profile["favorites"].append(food_name)
            self._save_profile()

    def get_favorites(self) -> List[str]:
        return self.profile["favorites"]

    def get_today_log(self) -> List[Dict[str, Any]]:
        """Get all food logged today."""
        today = date.today().isoformat()
        return [
            entry for entry in self.profile["history"] 
            if entry["date"] == today
        ]

    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get last N items eaten."""
        return self.profile["history"][-limit:]

    # --- Session Management ---
    def create_session(self, title: str = "New Chat") -> str:
        """Create a new chat session."""
        import uuid
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "messages": []
        }
        if "sessions" not in self.profile:
            self.profile["sessions"] = {}
        
        self.profile["sessions"][session_id] = session
        self._save_profile()
        return session_id

    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to a session."""
        if "sessions" not in self.profile:
             self.profile["sessions"] = {}
             
        if session_id not in self.profile["sessions"]:
            # Auto-create if not exists (fallback)
            self.create_session("Restored Session")
            
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.profile["sessions"][session_id]["messages"].append(msg)
        self._save_profile()

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get summary of all sessions for sidebar."""
        if "sessions" not in self.profile: return []
        
        # Return list sorted by date desc
        sessions = list(self.profile["sessions"].values())
        return sorted(sessions, key=lambda x: x["timestamp"], reverse=True)

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get full history of a session."""
        if "sessions" in self.profile and session_id in self.profile["sessions"]:
            return self.profile["sessions"][session_id]["messages"]
        return []

    # --- Long Term Facts ---
    # --- Long Term Facts ---
    def save_fact(self, fact: str):
        """Save a key user fact (Memory Graph)."""
        # 1. JSON (Backup)
        if "facts" not in self.profile:
            self.profile["facts"] = []
        
        if fact not in self.profile["facts"]:
            self.profile["facts"].append(fact)
            self._save_profile()
            
        # 2. SQLite Graph (Visual)
        try:
            from src.db.database import SessionLocal
            from src.services.graph_db import GraphService
            
            db = SessionLocal()
            svc = GraphService(db)
            # Add node for User (if not exists)
            user_node = svc.add_node(1, "User", "USER") # ID 1 is verified user
            
            # Add node for Fact
            # Heuristic: "I am vegan" -> Node: "Vegan"
            label = fact.replace("I am ", "").replace("i am ", "").strip().title()
            fact_node = svc.add_node(1, label, "FACT")
            
            # Link
            svc.add_edge(user_node.id, fact_node.id, "IS")
            db.close()
            print(f"🕸️ Added to Graph: User -> IS -> {label}")
        except Exception as e:
            print(f"⚠️ Graph DB Error: {e}")

    def get_facts(self) -> List[str]:
        return self.profile.get("facts", [])
