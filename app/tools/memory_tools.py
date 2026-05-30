from typing import Dict, Any
from app.memory.memory_store import user_memory
from app.database.db import log_agent_action

def memory_store(key: str, value: str) -> Dict[str, Any]:
    """Stores a fact or preference about the user to customize future responses."""
    try:
        user_memory.remember(key, value)
        log_agent_action("MemoryAgent", "memory_store", f"Remembered key '{key}': '{value}'")
        return {"success": True, "message": f"Successfully remembered '{key}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def memory_retrieve() -> Dict[str, Any]:
    """Retrieves all remembered facts and preferences about the user."""
    try:
        memories = user_memory.retrieve_all()
        log_agent_action("MemoryAgent", "memory_retrieve", "Retrieved remembered facts")
        return {"success": True, "data": memories}
    except Exception as e:
        return {"success": False, "error": str(e)}
