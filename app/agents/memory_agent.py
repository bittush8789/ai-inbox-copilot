import json
import logging
from app.services.groq_service import groq_service
from app.memory.memory_store import user_memory

logger = logging.getLogger("memory_agent")

def analyze_user_preference_statement(statement: str) -> bool:
    """
    Parses user conversation statement. If it contains preference instructions,
    automatically extracts the key/value and saves it to SQLite memory.
    """
    prompt = f"""You are the Memory Agent. Analyze the statement below.
Statement: "{statement}"

Decide if the user is explicitly requesting the assistant to remember something, stating a preference, writing style interest, or tone choice.
If they are, extract a concise key (e.g., "writing_style", "interest_mlops", "preferred_tone") and value.

Provide your response in raw JSON format:
{{
  "should_remember": true or false,
  "key": "concise lowercase key, or null",
  "value": "extracted preference statement, or null"
}}
"""
    try:
        response_text = groq_service.get_completion(prompt, json_mode=True)
        data = json.loads(response_text)
        if data.get("should_remember") and data.get("key") and data.get("value"):
            user_memory.remember(data["key"].strip().lower(), data["value"].strip())
            return True
        return False
    except Exception as e:
        logger.error(f"Memory Agent parsing failed: {e}")
        return False
