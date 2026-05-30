import logging
import datetime
import json
from typing import Generator, Dict, Any
from app.gmail.client import fetch_email_list, fetch_email_details
from app.gmail.parser import parse_gmail_message
from app.database.db import (
    email_exists, save_email_record, save_task, save_meeting, add_sync_log, SessionLocal
)
from app.agents.inbox_agent import analyze_incoming_email
from app.agents.task_agent import extract_tasks_and_meetings
from app.rag.chroma_client import rag_store

logger = logging.getLogger("gmail_sync_service")

def sync_gmail_inbox_generator(limit: int) -> Generator[Dict[str, Any], None, None]:
    """
    Generator-based Gmail sync engine.
    Yields real-time step status, completion percentages, and running stats.
    """
    stats = {
        "requested": limit,
        "fetched": 0,
        "processed": 0,
        "duplicates": 0,
        "urgent": 0,
        "tasks": 0,
        "meetings": 0,
        "jobs": 0,
        "invoices": 0
    }

    # --- STEP 1: Fetching emails ---
    yield {"step": 1, "msg": "Step 1: Fetching emails from Gmail API...", "percentage": 0.1, "stats": stats}
    
    try:
        messages = fetch_email_list(limit=limit)
        stats["fetched"] = len(messages)
    except Exception as e:
        logger.error(f"Gmail sync failed at listing fetch: {e}")
        add_sync_log(0, 0, 1)
        raise RuntimeError("Unable to sync emails. Please try again.")

    if not messages:
        yield {"step": 6, "msg": "Step 6: Sync complete. No new emails found.", "percentage": 1.0, "stats": stats}
        add_sync_log(0, 0, 0)
        return

    # Process each email
    total_messages = len(messages)
    
    for idx, msg in enumerate(messages):
        msg_id = msg["id"]
        
        # Calculate current progress percentage (scale between 15% and 95%)
        current_percent = 0.15 + (idx / total_messages) * 0.80
        
        # --- STEP 2: Analyzing email duplication ---
        yield {
            "step": 2,
            "msg": f"Step 2: Checking email {idx+1}/{total_messages} for duplicates...",
            "percentage": current_percent,
            "stats": stats
        }
        
        if email_exists(msg_id):
            stats["duplicates"] += 1
            continue

        try:
            # Fetch details
            raw_msg = fetch_email_details(msg_id)
            parsed = parse_gmail_message(raw_msg)
            
            # --- STEP 3: Generating summaries & categories ---
            yield {
                "step": 3,
                "msg": f"Step 3: Analyzing content and generating summary for: '{parsed['subject'][:30]}...' (email {idx+1}/{total_messages})",
                "percentage": current_percent + (0.05 / total_messages),
                "stats": stats
            }
            
            # Run Inbox agent analysis
            analysis = analyze_incoming_email(parsed["subject"], parsed["body"])
            
            if analysis["priority"] == "High":
                stats["urgent"] += 1
            if analysis["category"] == "Job" or "hiring" in parsed["subject"].lower() or "opportunity" in parsed["subject"].lower():
                stats["jobs"] += 1
            if analysis["category"] == "Finance" or "invoice" in parsed["subject"].lower() or "bill" in parsed["subject"].lower():
                stats["invoices"] += 1

            # --- STEP 4: Extracting tasks & calendar items ---
            yield {
                "step": 4,
                "msg": f"Step 4: Extracting tasks and meetings from: '{parsed['subject'][:30]}...'",
                "percentage": current_percent + (0.10 / total_messages),
                "stats": stats
            }
            
            extracted = extract_tasks_and_meetings(parsed["subject"], parsed["body"])
            
            # Save Email Record
            email_rec = save_email_record(
                gmail_message_id=parsed["gmail_message_id"],
                thread_id=parsed["thread_id"],
                sender=parsed["sender"],
                recipient=parsed["recipient"],
                subject=parsed["subject"],
                body=parsed["body"],
                summary=analysis["summary"],
                category=analysis["category"],
                priority=analysis["priority"],
                labels=parsed["labels"]
            )
            
            # Save extracted tasks
            for t in extracted["tasks"]:
                save_task(t["task"], t["deadline"], t["priority"], t["responsible_person"], email_rec.id)
                stats["tasks"] += 1
                
            # Save extracted meetings
            for m in extracted["meetings"]:
                save_meeting(m["title"], m["start_time"], m["end_time"], m["organizer"], email_rec.id)
                stats["meetings"] += 1
                if email_rec.category != "Meeting":
                    # Update category to Meeting if scheduled events were found
                    db = SessionLocal()
                    try:
                        from app.database.db import SessionLocal
                        from app.database.models import EmailRecord as ModelEmail
                        e_rec = db.query(ModelEmail).filter(ModelEmail.id == email_rec.id).first()
                        if e_rec:
                            e_rec.category = "Meeting"
                            db.commit()
                    except Exception:
                        pass
                    finally:
                        db.close()

            # --- STEP 5: Updating ChromaDB vector store ---
            yield {
                "step": 5,
                "msg": f"Step 5: Updating semantic vectors index for: '{parsed['subject'][:30]}...'",
                "percentage": current_percent + (0.15 / total_messages),
                "stats": stats
            }
            
            rag_store.add_email(
                email_id=email_rec.id,
                subject=email_rec.subject,
                sender=email_rec.sender or "Unknown",
                body=email_rec.body,
                summary=email_rec.summary or ""
            )
            
            stats["processed"] += 1
            
        except Exception as e:
            logger.error(f"Failed to process individual message ID {msg_id}: {e}")
            # Continue to next message to prevent entire batch fail
            continue
            
    # Write to local SyncLog audit
    try:
        add_sync_log(
            emails_synced=stats["processed"] + stats["duplicates"],
            success_count=stats["processed"],
            failed_count=stats["fetched"] - (stats["processed"] + stats["duplicates"])
        )
    except Exception:
        pass

    # --- STEP 6: Sync complete ---
    yield {
        "step": 6,
        "msg": "Step 6: Sync complete. Database and search indexes updated.",
        "percentage": 1.0,
        "stats": stats
    }
