import json
import logging
from app.services.groq_service import groq_service

logger = logging.getLogger("task_agent")

def extract_tasks_and_meetings(subject: str, body: str) -> dict:
    """Extracts lists of tasks and meetings from the email text."""
    prompt = f"""You are the Task Agent. Analyze the email below and extract any actionable tasks and scheduled meetings/events.

Subject: {subject}
Body: {body}

Provide your response in raw JSON format matching this schema:
{{
  "tasks": [
    {{
      "task": "Specific description of the action items",
      "deadline": "When it is due, or null",
      "priority": "High, Medium, or Low",
      "responsible_person": "Name of the person, or null"
    }}
  ],
  "meetings": [
    {{
      "title": "Meeting title or agenda topic",
      "start_time": "Date/Time of meeting, or null",
      "end_time": "Ending time, or null",
      "organizer": "Who is running the meeting, or null"
    }}
  ]
}}
"""
    try:
        response_text = groq_service.get_completion(prompt, json_mode=True)
        data = json.loads(response_text)
        return {
            "tasks": data.get("tasks", []),
            "meetings": data.get("meetings", [])
        }
    except Exception as e:
        logger.error(f"Task extraction failed: {e}")
        return {"tasks": [], "meetings": []}
