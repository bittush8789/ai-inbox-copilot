from typing import Dict, Any, List
from app.database.db import save_memory, get_all_memories

class MemoryStore:
    """
    Client wrapper for accessing stored user context, preferences, and tones.
    """
    def remember(self, key: str, value: str):
        """Stores a user preference key-value pair in SQLite."""
        save_memory(key, value)

    def retrieve_all(self) -> Dict[str, str]:
        """Retrieves all remembered facts as a dictionary."""
        records = get_all_memories()
        return {record.key: record.value for record in records}

    def get_context_string(self) -> str:
        """Formulates a clean profile context string for agent injections."""
        memories = self.retrieve_all()
        if not memories:
            return "No custom user preferences stored yet."
            
        lines = []
        for k, v in memories.items():
            lines.append(f"- **{k.title()}**: {v}")
        return "\n".join(lines)

# Instantiate singleton memory client
user_memory = MemoryStore()
