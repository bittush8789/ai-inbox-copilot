import json
import logging
from app.services.groq_service import groq_service

logger = logging.getLogger("inbox_agent")

CATEGORIES = {"Job", "Personal", "Finance", "Meeting", "Newsletter", "Marketing", "Security", "Support"}

def analyze_incoming_email(subject: str, body: str) -> dict:
    """
    Analyzes an email to extract category, priority, and a quick summary.
    """
    prompt = f"""You are the Inbox Agent of an email copilot system. Your task is to analyze the email below and categorize it.

Email Subject: {subject}
Email Body:
{body}

Classify the email into one of these exact categories: Job, Personal, Finance, Meeting, Newsletter, Marketing, Security, Support.
Determine the priority level: High, Medium, or Low (High for tight deadlines under 48h, urgency indicators, bills due immediately, security alerts, or important job interviews).
Generate a concise 1-sentence summary of the main point.

Provide your response in raw JSON format matching this schema:
{{
  "category": "One of the listed categories",
  "priority": "High, Medium, or Low",
  "summary": "1-sentence summary of the email"
}}
"""
    try:
        response_text = groq_service.get_completion(prompt, json_mode=True)
        data = json.loads(response_text)
        category = data.get("category", "Support").strip().title()
        if category not in CATEGORIES:
            category = "Support"
            
        priority = data.get("priority", "Low").strip().title()
        if priority not in {"High", "Medium", "Low"}:
            priority = "Low"
            
        return {
            "category": category,
            "priority": priority,
            "summary": data.get("summary", "(No summary generated)")
        }
    except Exception as e:
        logger.error(f"InboxAgent analysis failed: {e}")
        return {
            "category": "Support",
            "priority": "Medium",
            "summary": "Failed to auto-analyze email content."
        }
