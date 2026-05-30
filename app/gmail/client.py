import base64
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional
from app.gmail.auth import get_gmail_service

def fetch_email_list(
    limit: int = 10,
    unread_only: bool = False,
    query: Optional[str] = None
) -> List[Dict[str, str]]:
    """Retrieves message headers list from Gmail matching query criteria."""
    service = get_gmail_service()
    q_parts = []
    if unread_only:
        q_parts.append("is:unread")
    if query:
        q_parts.append(query)
    q_str = " ".join(q_parts) if q_parts else None
    
    response = service.users().messages().list(
        userId="me",
        q=q_str,
        maxResults=limit
    ).execute()
    
    return response.get("messages", [])

def fetch_email_details(message_id: str) -> Dict[str, Any]:
    """Retrieves a single email message detail by ID."""
    service = get_gmail_service()
    return service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

def get_thread_messages(thread_id: str) -> List[Dict[str, Any]]:
    """Retrieves all messages in a thread by ID."""
    service = get_gmail_service()
    thread = service.users().threads().get(userId="me", id=thread_id).execute()
    return thread.get("messages", [])

def send_email(to: str, subject: str, body: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """Sends a new email message using MIME structure."""
    service = get_gmail_service()
    
    mime_message = MIMEText(body)
    mime_message["to"] = to
    mime_message["subject"] = subject
    
    raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("utf-8")
    
    body_payload = {"raw": raw_message}
    if thread_id:
        body_payload["threadId"] = thread_id
        
    return service.users().messages().send(
        userId="me",
        body=body_payload
    ).execute()

def reply_to_email(thread_id: str, to: str, subject: str, body: str) -> Dict[str, Any]:
    """Constructs and sends a reply message targeting a specific thread."""
    messages = get_thread_messages(thread_id)
    if not messages:
        # Fallback to general sending if thread not found
        return send_email(to, subject, body, thread_id=thread_id)
        
    # Get last message headers for thread threading context
    last_msg = messages[-1]
    last_msg_details = fetch_email_details(last_msg["id"])
    headers = last_msg_details.get("payload", {}).get("headers", [])
    
    # Extract Message-ID header for threading
    msg_id_val = ""
    for h in headers:
        if h.get("name", "").lower() == "message-id":
            msg_id_val = h.get("value", "")
            break
            
    service = get_gmail_service()
    
    mime_message = MIMEText(body)
    mime_message["to"] = to
    mime_message["subject"] = subject
    if msg_id_val:
        mime_message["In-Reply-To"] = msg_id_val
        mime_message["References"] = msg_id_val
        
    raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode("utf-8")
    
    return service.users().messages().send(
        userId="me",
        body={
            "raw": raw_message,
            "threadId": thread_id
        }
    ).execute()

def archive_email(message_id: str) -> Dict[str, Any]:
    """Archives an email by removing the INBOX label."""
    service = get_gmail_service()
    return service.users().messages().batchModify(
        userId="me",
        body={
            "ids": [message_id],
            "removeLabelIds": ["INBOX"]
        }
    ).execute()

def mark_as_read(message_id: str) -> Dict[str, Any]:
    """Marks an email as read by removing UNREAD label."""
    service = get_gmail_service()
    return service.users().messages().batchModify(
        userId="me",
        body={
            "ids": [message_id],
            "removeLabelIds": ["UNREAD"]
        }
    ).execute()

def mark_as_unread(message_id: str) -> Dict[str, Any]:
    """Marks an email as unread by adding UNREAD label."""
    service = get_gmail_service()
    return service.users().messages().batchModify(
        userId="me",
        body={
            "ids": [message_id],
            "addLabelIds": ["UNREAD"]
        }
    ).execute()
