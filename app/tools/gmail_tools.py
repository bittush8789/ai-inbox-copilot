import logging
from typing import Dict, Any, List, Optional
from app.gmail.client import (
    fetch_email_details, fetch_email_list, archive_email,
    mark_as_read, mark_as_unread, get_thread_messages
)
from app.database.db import create_draft, log_agent_action

logger = logging.getLogger("gmail_tools")

def gmail_read(message_id: str) -> Dict[str, Any]:
    """Retrieves full details of a specific Gmail message."""
    try:
        details = fetch_email_details(message_id)
        log_agent_action("InboxAgent", "gmail_read", f"Read message ID: {message_id}")
        return {"success": True, "data": details}
    except Exception as e:
        logger.error(f"gmail_read failed: {e}")
        return {"success": False, "error": str(e)}

def gmail_search(query: str, limit: int = 10) -> Dict[str, Any]:
    """Queries and returns list of messages matching term criteria."""
    try:
        messages = fetch_email_list(limit=limit, query=query)
        log_agent_action("SearchAgent", "gmail_search", f"Searched Gmail for: {query}")
        return {"success": True, "data": messages}
    except Exception as e:
        return {"success": False, "error": str(e)}

def gmail_send(to: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Creates an email draft in pending_approval state.
    Requires human-in-the-loop review before sending.
    """
    try:
        draft = create_draft(thread_id=None, to_email=to, subject=subject, body=body, status="pending_approval")
        log_agent_action("ReplyAgent", "gmail_send", f"Created draft reply to {to} awaiting approval.")
        return {
            "success": True,
            "message": "Draft created successfully. Awaiting human approval in UI.",
            "draft_id": draft.id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def gmail_reply(thread_id: str, to: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Creates an email thread reply draft in pending_approval state.
    Requires human-in-the-loop review before sending.
    """
    try:
        draft = create_draft(thread_id=thread_id, to_email=to, subject=subject, body=body, status="pending_approval")
        log_agent_action("ReplyAgent", "gmail_reply", f"Created draft reply to thread {thread_id} awaiting approval.")
        return {
            "success": True,
            "message": "Draft reply created successfully. Awaiting human approval in UI.",
            "draft_id": draft.id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def gmail_archive(message_id: str) -> Dict[str, Any]:
    """Removes message from INBOX."""
    try:
        archive_email(message_id)
        log_agent_action("InboxAgent", "gmail_archive", f"Archived message ID: {message_id}")
        return {"success": True, "message": "Email archived successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def gmail_mark_read(message_id: str) -> Dict[str, Any]:
    """Removes UNREAD label."""
    try:
        mark_as_read(message_id)
        log_agent_action("InboxAgent", "gmail_mark_read", f"Marked message ID: {message_id} as read")
        return {"success": True, "message": "Email marked as read."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def gmail_mark_unread(message_id: str) -> Dict[str, Any]:
    """Applies UNREAD label."""
    try:
        mark_as_unread(message_id)
        log_agent_action("InboxAgent", "gmail_mark_unread", f"Marked message ID: {message_id} as unread")
        return {"success": True, "message": "Email marked as unread."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def gmail_get_thread(thread_id: str) -> Dict[str, Any]:
    """Retrieves all emails associated with the given Thread ID."""
    try:
        messages = get_thread_messages(thread_id)
        log_agent_action("InboxAgent", "gmail_get_thread", f"Read thread ID: {thread_id}")
        return {"success": True, "data": messages}
    except Exception as e:
        return {"success": False, "error": str(e)}
