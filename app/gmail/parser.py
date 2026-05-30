import base64
import re
from typing import Dict, Any, List

def parse_header(headers: List[Dict[str, str]], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""

def clean_html(raw_html: str) -> str:
    clean = re.sub(r'<(script|style).*?>.*?</\1>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<[^>]*>', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def decode_body(payload: Dict[str, Any]) -> str:
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")
    
    if body_data:
        decoded_bytes = base64.urlsafe_b64decode(body_data)
        decoded_str = decoded_bytes.decode("utf-8", errors="ignore")
        if mime_type == "text/html":
            return clean_html(decoded_str)
        return decoded_str
        
    parts = payload.get("parts", [])
    text_content = ""
    html_content = ""
    
    for part in parts:
        part_mime = part.get("mimeType", "")
        part_body = decode_body(part)
        
        if part_mime == "text/plain":
            text_content += part_body
        elif part_mime == "text/html":
            html_content += part_body
        elif part.get("parts"):
            text_content += decode_body(part)
            
    if text_content.strip():
        return text_content
    return html_content

def parse_gmail_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    msg_id = message_data.get("id")
    thread_id = message_data.get("threadId")
    labels = message_data.get("labelIds", [])
    
    payload = message_data.get("payload", {})
    headers = payload.get("headers", [])
    
    subject = parse_header(headers, "Subject") or "(No Subject)"
    sender = parse_header(headers, "From") or "Unknown"
    recipient = parse_header(headers, "To") or "Unknown"
    
    body = decode_body(payload)
    if not body.strip():
        snippet = message_data.get("snippet", "")
        body = snippet or "(Empty email body)"
        
    internal_date = int(message_data.get("internalDate", 0)) / 1000.0
    
    return {
        "gmail_message_id": msg_id,
        "thread_id": thread_id,
        "sender": sender,
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "labels": labels,
        "internal_timestamp": internal_date
    }
