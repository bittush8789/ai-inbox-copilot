import logging
from typing import List, Dict, Any
from app.services.groq_service import groq_service

logger = logging.getLogger("summary_agent")

def generate_email_summary(subject: str, sender: str, body: str) -> str:
    """Generates a detailed summary of a single email."""
    prompt = f"""You are the Summarization Agent. Write a concise but informative summary of the email below.
Subject: {subject}
From: {sender}
Body: {body}

Response format:
- Summary: A 2-sentence summary.
- Key Points: 3 bullet points of critical details.
- Action Items: Any explicit tasks.
- Deadlines: Any dates mentioned.
"""
    try:
        return groq_service.get_completion(prompt, json_mode=False)
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        return "Summary generation failed."

def compile_digest(emails: List[Dict[str, Any]], digest_type: str = "daily") -> str:
    """Compiles a summary digest of multiple emails."""
    if not emails:
        return f"No emails available to generate a {digest_type} digest."
        
    context = ""
    for idx, e in enumerate(emails):
        context += f"\nEmail #{idx+1} | Subject: {e['subject']} | Sender: {e['sender']} | Summary: {e.get('summary', '')}\n"
        
    prompt = f"""You are the Summarization Agent. Create a professional {digest_type} digest of the following emails:
{context}

Format:
- Top-level overview
- High priority alerts (if any)
- Pending meetings
- Consolidated action items list
"""
    try:
        return groq_service.get_completion(prompt, json_mode=False)
    except Exception as e:
        logger.error(f"Failed to compile digest: {e}")
        return f"Failed to compile {digest_type} digest."
