import os
import json
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker, Session
from app.database.models import Base, User, EmailRecord, EmailThread, TaskRecord, MeetingRecord, DraftRecord, MemoryRecord, AgentAction, EmailEmbedding

DB_PATH = "sqlite:///emails.db"

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db_session() -> Session:
    return SessionLocal()

def email_exists(gmail_message_id: str) -> bool:
    if not gmail_message_id:
        return False
    db = SessionLocal()
    try:
        return db.query(EmailRecord).filter(EmailRecord.gmail_message_id == gmail_message_id).first() is not None
    finally:
        db.close()

def save_email_record(
    gmail_message_id: Optional[str],
    thread_id: Optional[str],
    sender: Optional[str],
    recipient: Optional[str],
    subject: str,
    body: str,
    summary: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    labels: Optional[List[str]] = None
) -> EmailRecord:
    db = SessionLocal()
    try:
        labels_str = json.dumps(labels) if labels else None
        
        # Check thread count
        if thread_id:
            thread = db.query(EmailThread).filter(EmailThread.thread_id == thread_id).first()
            if thread:
                thread.emails_count += 1
                thread.last_message_date = datetime.datetime.utcnow()
            else:
                thread = EmailThread(thread_id=thread_id, subject=subject, emails_count=1)
                db.add(thread)
                
        email_rec = EmailRecord(
            gmail_message_id=gmail_message_id,
            thread_id=thread_id,
            sender=sender,
            recipient=recipient,
            subject=subject,
            body=body,
            summary=summary,
            category=category,
            priority=priority,
            labels=labels_str
        )
        db.add(email_rec)
        db.commit()
        db.refresh(email_rec)
        return email_rec
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def save_task(
    task: str,
    deadline: Optional[str],
    priority: Optional[str],
    responsible_person: Optional[str],
    email_id: Optional[int] = None
) -> TaskRecord:
    db = SessionLocal()
    try:
        task_rec = TaskRecord(
            task=task,
            deadline=deadline,
            priority=priority,
            responsible_person=responsible_person,
            email_id=email_id
        )
        db.add(task_rec)
        db.commit()
        db.refresh(task_rec)
        return task_rec
    finally:
        db.close()

def save_meeting(
    title: str,
    start_time: Optional[str],
    end_time: Optional[str],
    organizer: Optional[str],
    email_id: Optional[int] = None
) -> MeetingRecord:
    db = SessionLocal()
    try:
        mtg_rec = MeetingRecord(
            title=title,
            start_time=start_time,
            end_time=end_time,
            organizer=organizer,
            email_id=email_id
        )
        db.add(mtg_rec)
        db.commit()
        db.refresh(mtg_rec)
        return mtg_rec
    finally:
        db.close()

def create_draft(
    thread_id: Optional[str],
    to_email: str,
    subject: Optional[str],
    body: str,
    status: str = "pending_approval"
) -> DraftRecord:
    db = SessionLocal()
    try:
        draft = DraftRecord(
            thread_id=thread_id,
            to_email=to_email,
            subject=subject,
            body=body,
            status=status
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft
    finally:
        db.close()

def get_draft(draft_id: int) -> Optional[DraftRecord]:
    db = SessionLocal()
    try:
        return db.query(DraftRecord).filter(DraftRecord.id == draft_id).first()
    finally:
        db.close()

def update_draft_status(draft_id: int, status: str):
    db = SessionLocal()
    try:
        draft = db.query(DraftRecord).filter(DraftRecord.id == draft_id).first()
        if draft:
            draft.status = status
            db.commit()
            return True
        return False
    finally:
        db.close()

def get_pending_drafts() -> List[DraftRecord]:
    db = SessionLocal()
    try:
        # Return newest drafts awaiting approval
        return db.query(DraftRecord).filter(DraftRecord.status == "pending_approval").order_by(DraftRecord.created_at.desc()).all()
    finally:
        db.close()

def save_memory(key: str, value: str) -> MemoryRecord:
    db = SessionLocal()
    try:
        mem = db.query(MemoryRecord).filter(MemoryRecord.key == key).first()
        if mem:
            mem.value = value
        else:
            mem = MemoryRecord(key=key, value=value)
            db.add(mem)
        db.commit()
        db.refresh(mem)
        return mem
    finally:
        db.close()

def get_all_memories() -> List[MemoryRecord]:
    db = SessionLocal()
    try:
        return db.query(MemoryRecord).all()
    finally:
        db.close()

def log_agent_action(agent_name: str, action_taken: str, details: Optional[str] = None):
    db = SessionLocal()
    try:
        act = AgentAction(agent_name=agent_name, action_taken=action_taken, details=details)
        db.add(act)
        db.commit()
    finally:
        db.close()

def get_all_emails(limit: int = 100) -> List[EmailRecord]:
    db = SessionLocal()
    try:
        return db.query(EmailRecord).order_by(EmailRecord.created_at.desc()).limit(limit).all()
    finally:
        db.close()

def get_stats() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        total = db.query(EmailRecord).count()
        unread = db.query(EmailRecord).filter(EmailRecord.labels.like("%UNREAD%")).count()
        urgent = db.query(EmailRecord).filter(EmailRecord.priority == "High").count()
        
        # Tasks & Meetings counts
        tasks = db.query(TaskRecord).count()
        meetings = db.query(MeetingRecord).count()
        
        # Job opportunities (Category Job/Work/Recruiter)
        jobs = db.query(EmailRecord).filter(
            or_(
                EmailRecord.category.ilike("%job%"),
                EmailRecord.subject.ilike("%hiring%"),
                EmailRecord.subject.ilike("%opportunity%")
            )
        ).count()
        
        # Invoices
        invoices = db.query(EmailRecord).filter(
            or_(
                EmailRecord.category.ilike("%finance%"),
                EmailRecord.subject.ilike("%invoice%"),
                EmailRecord.subject.ilike("%bill%")
            )
        ).count()
        
        return {
            "total": total,
            "unread": unread,
            "urgent": urgent,
            "tasks": tasks,
            "meetings": meetings,
            "jobs": jobs,
            "invoices": invoices
        }
    finally:
        db.close()

def add_sync_log(emails_synced: int, success_count: int, failed_count: int):
    db = SessionLocal()
    try:
        from app.database.models import SyncLog
        log = SyncLog(
            emails_synced=emails_synced,
            success_count=success_count,
            failed_count=failed_count
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_sync_logs(limit: int = 50):
    db = SessionLocal()
    try:
        from app.database.models import SyncLog
        return db.query(SyncLog).order_by(SyncLog.synced_at.desc()).limit(limit).all()
    finally:
        db.close()

