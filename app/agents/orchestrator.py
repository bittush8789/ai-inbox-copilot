import logging
from typing import List, Dict, Any, TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from app.services.groq_service import groq_service
from app.database.db import get_all_emails, get_pending_drafts
from app.memory.memory_store import user_memory
from app.agents.inbox_agent import analyze_incoming_email
from app.agents.summary_agent import generate_email_summary, compile_digest
from app.agents.reply_agent import generate_reply_body
from app.agents.task_agent import extract_tasks_and_meetings
from app.agents.search_agent import run_semantic_email_search
from app.agents.memory_agent import analyze_user_preference_statement

logger = logging.getLogger("agent_orchestrator")

class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    current_agent: str
    context_emails: List[Dict[str, Any]]
    action_drafts: List[Dict[str, Any]]
    query: str
    response: str

# 1. Routing / Intent Analysis Node
def route_intent_node(state: AgentState) -> AgentState:
    query = state["query"]
    logger.info(f"Orchestrator routing query: {query}")
    
    # Run memory agent to see if it needs to learn user preferences
    analyze_user_preference_statement(query)
    
    prompt = f"""You are the Inbox Router Agent. Analyze the user query below and route it to the appropriate specialized agent.
User Query: "{query}"

Available Agents:
- summarizer: For queries asking to summarize emails, write digests, or compile overall logs.
- replier: For queries requesting to write, generate, compose, or edit drafts/replies to emails.
- task_extractor: For queries asking to show tasks, extract deadlines, find meetings, or compile follow-up items.
- search_rag: For queries asking to search or find specific topics, senders, terms, jobs, or invoices (semantic retrieval queries).
- general: For general chat, greetings, or help requests.

Provide your response in raw JSON format:
{{
  "route": "summarizer, replier, task_extractor, search_rag, or general"
}}
"""
    try:
        import json
        response_text = groq_service.get_completion(prompt, json_mode=True)
        data = json.loads(response_text)
        route = data.get("route", "general").strip().lower()
    except Exception:
        route = "general"
        
    state["current_agent"] = route
    return state

# 2. Summarizer Agent Node
def summarizer_node(state: AgentState) -> AgentState:
    emails = get_all_emails(limit=25)
    emails_data = [
        {
            "subject": e.subject,
            "sender": e.sender or "Unknown",
            "body": e.body,
            "summary": e.summary or ""
        } for e in emails
    ]
    
    query = state["query"]
    if "digest" in query.lower() or "summarize" in query.lower():
        state["response"] = compile_digest(emails_data, "inbox")
    else:
        # Default summarize latest
        state["response"] = compile_digest(emails_data[:5], "latest emails")
    return state

# 3. Replier Agent Node
def replier_node(state: AgentState) -> AgentState:
    query = state["query"]
    emails = get_all_emails(limit=10)
    
    # Try finding the target email to reply to
    target_email = None
    for e in emails:
        # Match keywords from query to email subjects
        words = query.lower().split()
        matches = [w for w in words if w in e.subject.lower() or w in (e.sender or "").lower()]
        if len(matches) >= 2:
            target_email = e
            break
            
    if not target_email and emails:
        target_email = emails[0]
        
    if not target_email:
        state["response"] = "No emails found in your inbox to draft replies to."
        return state
        
    # Check for unmonitored sender addresses (Noreply)
    sender_clean = (target_email.sender or "").lower()
    if "noreply" in sender_clean or "no-reply" in sender_clean or "donotreply" in sender_clean:
        state["response"] = "This email address does not accept replies."
        return state
        
    # Get user memory tone
    context = user_memory.get_context_string()
    
    tone = "professional"
    if "friendly" in query.lower():
        tone = "friendly"
    elif "formal" in query.lower():
        tone = "formal"
        
    reply_body = generate_reply_body(
        original_subject=target_email.subject,
        original_sender=target_email.sender or "Unknown",
        original_body=target_email.body,
        tone=tone,
        user_context=context
    )
    
    # Store draft in pending_approval
    from app.database.db import create_draft
    draft = create_draft(
        thread_id=target_email.thread_id,
        to_email=target_email.sender or "Unknown",
        subject=f"Re: {target_email.subject}",
        body=reply_body
    )
    
    state["response"] = f"I've drafted a {tone} reply to **{target_email.sender}** regarding *{target_email.subject}*. Please review and approve it below!"
    return state

# 4. Task Extractor Node
def task_extractor_node(state: AgentState) -> AgentState:
    emails = get_all_emails(limit=25)
    
    extracted_md = "### 📋 Extracted Tasks & Meetings:\n"
    has_content = False
    
    from app.database.db import save_task, save_meeting
    for email in emails:
        # If tasks not already extracted, run extraction
        if not email.tasks and not email.meetings:
            extracted = extract_tasks_and_meetings(email.subject, email.body)
            for t in extracted["tasks"]:
                save_task(t["task"], t["deadline"], t["priority"], t["responsible_person"], email.id)
            for m in extracted["meetings"]:
                save_meeting(m["title"], m["start_time"], m["end_time"], m["organizer"], email.id)
                
        # Re-fetch email with relations (session closed in db.py helper, but we query relations)
        if email.tasks or email.meetings:
            has_content = True
            extracted_md += f"\n✉️ **Email**: *{email.subject}*\n"
            for t in email.tasks:
                dl_text = f" (Due: {t.deadline})" if t.deadline else ""
                extracted_md += f"- [ ] **Task**: {t.task}{dl_text}\n"
            for m in email.meetings:
                extracted_md += f"- 📅 **Meeting**: {m.title} ({m.start_time or 'TBD'})\n"
                
    if not has_content:
        state["response"] = "No pending tasks or meetings found in your inbox."
    else:
        state["response"] = extracted_md
    return state

# 5. Search RAG Node
def search_rag_node(state: AgentState) -> AgentState:
    query = state["query"]
    state["response"] = run_semantic_email_search(query)
    return state

# 6. General / Conversational fallback Node
def general_chat_node(state: AgentState) -> AgentState:
    query = state["query"]
    prompt = f"""You are AI Inbox Copilot. Answer the user's general conversational input.
Input: {query}
"""
    try:
        state["response"] = groq_service.get_completion(prompt, json_mode=False)
    except Exception as e:
        state["response"] = "We couldn't process your request. Please try again."
    return state

# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("route_intent", route_intent_node)
workflow.add_node("summarizer", summarizer_node)
workflow.add_node("replier", replier_node)
workflow.add_node("task_extractor", task_extractor_node)
workflow.add_node("search_rag", search_rag_node)
workflow.add_node("general", general_chat_node)

workflow.set_entry_point("route_intent")

def state_router(state: AgentState) -> str:
    agent = state.get("current_agent", "general")
    if agent in {"summarizer", "replier", "task_extractor", "search_rag", "general"}:
        return agent
    return "general"

workflow.add_conditional_edges(
    "route_intent",
    state_router,
    {
        "summarizer": "summarizer",
        "replier": "replier",
        "task_extractor": "task_extractor",
        "search_rag": "search_rag",
        "general": "general"
    }
)

workflow.add_edge("summarizer", END)
workflow.add_edge("replier", END)
workflow.add_edge("task_extractor", END)
workflow.add_edge("search_rag", END)
workflow.add_edge("general", END)

# Compile graph
graph = workflow.compile()

def process_agent_query(query: str) -> str:
    """Processes user query through the LangGraph Multi-Agent workflow."""
    initial_state = {
        "messages": [],
        "current_agent": "",
        "context_emails": [],
        "action_drafts": [],
        "query": query,
        "response": ""
    }
    try:
        final_state = graph.invoke(initial_state)
        return final_state.get("response", "We couldn't process your request. Please try again.")
    except Exception as e:
        logger.error(f"LangGraph execution failed: {e}")
        return "We couldn't process your request. Please reconnect Gmail."
