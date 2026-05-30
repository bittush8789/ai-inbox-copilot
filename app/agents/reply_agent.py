import logging
from app.services.groq_service import groq_service

logger = logging.getLogger("reply_agent")

def generate_reply_body(
    original_subject: str,
    original_sender: str,
    original_body: str,
    tone: str = "professional",
    user_context: str = ""
) -> str:
    """Generates a reply draft in the requested tone, injecting custom memory context."""
    prompt = f"""You are the Reply Agent. Draft a reply to the email below.
Tone: {tone}

User Preferences/Context:
{user_context}

Original Email details:
Subject: {original_subject}
From: {original_sender}
Body: {original_body}

Draft only the body of the reply message. Do not include subject lines or metadata headers. Make it natural and tailored to the requested tone.
"""
    try:
        return groq_service.get_completion(prompt, json_mode=False)
    except Exception as e:
        logger.error(f"Failed to generate reply draft: {e}")
        return "Failed to generate reply draft."
