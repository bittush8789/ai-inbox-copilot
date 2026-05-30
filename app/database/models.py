import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class EmailRecord(Base):
    __tablename__ = 'emails'
    id = Column(Integer, primary_key=True, autoincrement=True)
    gmail_message_id = Column(String(100), unique=True, index=True, nullable=True)
    thread_id = Column(String(100), index=True, nullable=True)
    sender = Column(String(255), nullable=True)
    recipient = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    priority = Column(String(20), nullable=True)
    labels = Column(Text, nullable=True)  # JSON-serialized list of labels
    synced_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    tasks = relationship("TaskRecord", back_populates="email", cascade="all, delete-orphan")
    meetings = relationship("MeetingRecord", back_populates="email", cascade="all, delete-orphan")

class EmailThread(Base):
    __tablename__ = 'email_threads'
    thread_id = Column(String(100), primary_key=True)
    subject = Column(String(255), nullable=True)
    emails_count = Column(Integer, default=1)
    last_message_date = Column(DateTime, default=datetime.datetime.utcnow)

class TaskRecord(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    task = Column(Text, nullable=False)
    deadline = Column(String(100), nullable=True)
    priority = Column(String(20), nullable=True)
    responsible_person = Column(String(100), nullable=True)
    email_id = Column(Integer, ForeignKey('emails.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    email = relationship("EmailRecord", back_populates="tasks")

class MeetingRecord(Base):
    __tablename__ = 'meetings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    start_time = Column(String(100), nullable=True)
    end_time = Column(String(100), nullable=True)
    organizer = Column(String(255), nullable=True)
    email_id = Column(Integer, ForeignKey('emails.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    email = relationship("EmailRecord", back_populates="meetings")

class DraftRecord(Base):
    __tablename__ = 'drafts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(100), nullable=True)
    to_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    # Statuses: pending_approval, approved, sent, rejected
    status = Column(String(50), default="pending_approval")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MemoryRecord(Base):
    __tablename__ = 'memories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AgentAction(Base):
    __tablename__ = 'agent_actions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(100), nullable=False)
    action_taken = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class EmailEmbedding(Base):
    __tablename__ = 'email_embeddings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey('emails.id'), nullable=False)
    vector_id = Column(String(100), unique=True, nullable=False)
