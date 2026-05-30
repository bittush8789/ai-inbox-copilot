import streamlit as st
import datetime
import json
import os
import logging
logger = logging.getLogger("main")

from app.database.db import (
    init_db, get_stats, get_pending_drafts, update_draft_status,
    save_email_record, email_exists, get_draft, SessionLocal, get_all_emails
)
from app.database.models import DraftRecord, TaskRecord, MeetingRecord, EmailRecord
from app.gmail.auth import get_gmail_credentials, validate_gmail_setup, is_gmail_connected, get_connected_email, disconnect_gmail
from app.gmail.client import send_email, reply_to_email, fetch_email_list, fetch_email_details
from app.gmail.parser import parse_gmail_message
from app.agents.inbox_agent import analyze_incoming_email
from app.agents.orchestrator import process_agent_query
from app.services.groq_service import groq_service
from app.rag.chroma_client import rag_store
from app.ui.styles import inject_custom_css

# Initialize database
init_db()

# Inject design stylesheet
inject_custom_css()

# Session state initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# Initialize state dictionary
if "copilot_state" not in st.session_state:
    st.session_state.copilot_state = {
        "selected_email_id": None,
        "draft_id": None,
        "draft_content": "",
        "draft_recipient": "",
        "draft_subject": "",
        "pending_action": None,
        "approval_status": "IDLE",
        "last_tool_called": None,
        "conversation_context": {}
    }

# ----------------- INTENT DETECTION HELPERS -----------------
def is_approval_intent(query: str) -> bool:
    clean = query.strip().lower().rstrip('.!?')
    approval_phrases = {
        "send it", "send", "yes send", "approve", "proceed",
        "go ahead", "dispatch", "send email", "mail it", "yes"
    }
    return clean in approval_phrases

def execute_gmail_send_action(draft_id: int, edited_body: str) -> bool:
    db = SessionLocal()
    try:
        draft = db.query(DraftRecord).filter(DraftRecord.id == draft_id).first()
        if not draft:
            return False
            
        if draft.thread_id:
            reply_to_email(draft.thread_id, draft.to_email, draft.subject or "Reply", edited_body)
        else:
            send_email(draft.to_email, draft.subject or "Reply", edited_body)
            
        draft.status = "sent"
        db.commit()
        
        from app.database.db import log_agent_action
        log_agent_action("ReplyAgent", "gmail_send", f"Sent email to {draft.to_email}")
        
        st.session_state.copilot_state["approval_status"] = "EMAIL_SENT"
        st.session_state.copilot_state["pending_action"] = None
        return True
    except Exception as e:
        logger.error(f"gmail_send failed: {e}")
        st.session_state.copilot_state["approval_status"] = "FAILED"
        return False
    finally:
        db.close()

# ----------------- NATIVE DRAFT REVIEW DIALOG -----------------
@st.dialog("📩 Review Draft Message", width="large")
def show_draft_dialog(draft):
    st.markdown(f"**Recipient:** `{draft.to_email}`")
    st.markdown(f"**Subject:** `{draft.subject or 'Reply'}`")
    
    edited_body = st.text_area("Draft Body Content", draft.body, height=220)
    st.session_state.copilot_state["draft_content"] = edited_body
    
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    
    with col_dl1:
        if st.button("🚀 Send", type="primary", use_container_width=True):
            with st.spinner("Dispatching..."):
                if execute_gmail_send_action(draft.id, edited_body):
                    st.toast("Email Sent!")
                    st.rerun()
                else:
                    st.error("Unable to sync emails. Please try again.")
                    
    with col_dl2:
        if st.button("🗑️ Discard", use_container_width=True):
            update_draft_status(draft.id, "rejected")
            st.session_state.copilot_state["approval_status"] = "IDLE"
            st.session_state.copilot_state["pending_action"] = None
            st.toast("Draft discarded.")
            st.rerun()
            
    with col_dl3:
        if edited_body != draft.body:
            if st.button("💾 Save Changes", use_container_width=True):
                db = SessionLocal()
                try:
                    d_rec = db.query(DraftRecord).filter(DraftRecord.id == draft.id).first()
                    if d_rec:
                        d_rec.body = edited_body
                        db.commit()
                    st.toast("Saved!")
                    st.rerun()
                except Exception:
                    pass
                finally:
                    db.close()

# ================= TOP NAVIGATION BAR (GLASS EFFECT) =================
try:
    connected = is_gmail_connected()
except Exception:
    connected = False

st.markdown("<div class='glass-header'>", unsafe_allow_html=True)
col_nav_logo, col_nav_status, col_nav_btn = st.columns([2, 1.5, 1.5])

with col_nav_logo:
    st.markdown("<h3 style='margin:0; line-height: 48px;'><span class='saas-title'>🤖 AI Inbox Copilot</span></h3>", unsafe_allow_html=True)

with col_nav_status:
    if connected:
        email_addr = get_connected_email() or "Gmail account"
        st.markdown(f"<div style='text-align: right; line-height: 48px; font-size:0.9rem; color:#22C55E; font-weight:600;'>🟢 Connected: {email_addr}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align: right; line-height: 48px; font-size:0.9rem; color:#EF4444; font-weight:600;'>🔴 Gmail Disconnected</div>", unsafe_allow_html=True)

with col_nav_btn:
    col_sub_sync, col_sub_disc = st.columns([1, 1])
    with col_sub_sync:
        if connected:
            if st.button("🔄 Sync", key="nav_sync_btn", use_container_width=True):
                from app.gmail.sync_service import sync_gmail_inbox_generator
                progress_bar = st.progress(0.0)
                status_msg = st.empty()
                try:
                    for update in sync_gmail_inbox_generator(limit=10):
                        progress_bar.progress(update["percentage"])
                        status_msg.caption(update["msg"])
                    status_msg.empty()
                    progress_bar.empty()
                    st.toast("Sync Complete!")
                    st.rerun()
                except Exception:
                    st.error("Unable to sync emails. Please try again.")
        else:
            diagnostics = validate_gmail_setup()
            if diagnostics["credentials_exists"] and diagnostics["credentials_valid"]:
                if st.button("Link", key="nav_link_btn", type="primary", use_container_width=True):
                    try:
                        get_gmail_credentials()
                        st.toast("Connected!")
                        st.rerun()
                    except Exception:
                        st.error("Authentication failed.")
            else:
                st.caption("Missing credentials.json")
                
    with col_sub_disc:
        if connected:
            if st.button("Unlink", key="nav_disc_btn", type="primary", use_container_width=True):
                disconnect_gmail()
                st.toast("Disconnected.")
                st.rerun()
        else:
            st.caption("Disconnected")

st.markdown("</div>", unsafe_allow_html=True)

# ================= HERO HEADER SECTION =================
st.markdown("<h2 style='text-align: center; margin-top: 1.5rem; font-weight: 700; color: #F8FAFC;'>Your AI Assistant for Email</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color:#94A3B8; font-size:1.1rem; margin-bottom: 2.5rem;'>Securely connect Gmail, auto-extract tasks/meetings, and reply with custom AI models.</p>", unsafe_allow_html=True)

# ================= QUICK ACTION CHIPS =================
st.markdown("""<div class="chip-container" style="justify-content: center; margin-bottom: 2.5rem;">""", unsafe_allow_html=True)
col_c1, col_c2, col_c3, col_c4, col_c5, col_c6 = st.columns(6)
with col_c1:
    if st.button("📝 Summarize Inbox", key="c_sum", use_container_width=True):
        st.session_state.pending_query = "Summarize today's inbox"
        st.rerun()
with col_c2:
    if st.button("🚨 Urgent Emails", key="c_urg", use_container_width=True):
        st.session_state.pending_query = "Show urgent emails"
        st.rerun()
with col_c3:
    if st.button("📋 Tasks List", key="c_tsk", use_container_width=True):
        st.session_state.pending_query = "Show pending tasks"
        st.rerun()
with col_c4:
    if st.button("✍️ Draft Reply", key="c_rep", use_container_width=True):
        st.session_state.pending_query = "Draft a response to recruiter emails"
        st.rerun()
with col_c5:
    if st.button("📅 Meetings", key="c_mtg", use_container_width=True):
        st.session_state.pending_query = "Show calendar meetings"
        st.rerun()
with col_c6:
    if st.button("🧾 Invoices", key="c_inv", use_container_width=True):
        st.session_state.pending_query = "Show all bill and invoice emails"
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# ================= ACTIVE DRAFT MODAL OVERLAY TRIGGER =================
pending_drafts = get_pending_drafts()
if pending_drafts:
    active_draft = pending_drafts[0]
    st.session_state.copilot_state["draft_id"] = active_draft.id
    st.session_state.copilot_state["draft_recipient"] = active_draft.to_email
    st.session_state.copilot_state["draft_subject"] = active_draft.subject
    st.session_state.copilot_state["draft_content"] = active_draft.body
    st.session_state.copilot_state["pending_action"] = "SEND_EMAIL"
    st.session_state.copilot_state["approval_status"] = "WAITING_APPROVAL"
    
    st.markdown(f"""
        <div class="premium-card">
            <h4 style="margin: 0 0 0.5rem 0; color: #F8FAFC; font-weight: 600;">📩 Draft Message Pending Review</h4>
            <p class="muted-text" style="margin: 0;">You have an AI-composed response ready for <strong>{active_draft.to_email}</strong>. Please review, edit, or dispatch the message.</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Review Drafts", type="primary", use_container_width=True):
        show_draft_dialog(active_draft)
else:
    if st.session_state.copilot_state["approval_status"] == "WAITING_APPROVAL":
        st.session_state.copilot_state["approval_status"] = "IDLE"
        st.session_state.copilot_state["pending_action"] = None

# ================= CHAT TIMELINE AREA (80% WIDTH VIA CENTER CONTAINER CSS) =================
st.write("---")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Fixed input at bottom
user_input = st.chat_input("Ask about your inbox...")
if st.session_state.pending_query:
    user_input = st.session_state.pending_query
    st.session_state.pending_query = None

if user_input:
    is_waiting = st.session_state.copilot_state["approval_status"] == "WAITING_APPROVAL"
    draft_id = st.session_state.copilot_state["draft_id"]
    
    # 1. Approval Intent Intercept
    if is_waiting and is_approval_intent(user_input):
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.chat_message("assistant"):
            current_time = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M UTC")
            recipient = st.session_state.copilot_state["draft_recipient"]
            subject = st.session_state.copilot_state["draft_subject"]
            body_content = st.session_state.copilot_state["draft_content"]
            
            if execute_gmail_send_action(draft_id, body_content):
                response = f"""Email sent successfully.

**Recipient**: {recipient}
**Subject**: {subject}
**Timestamp**: {current_time}"""
                st.markdown(response)
            else:
                response = "We couldn't process your request. Please try again."
                st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()
        
    # 2. Duplicate Draft Prevention
    elif is_waiting and ("reply" in user_input.lower() or "draft" in user_input.lower() or "write" in user_input.lower()):
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("assistant"):
            response = "You already have a draft waiting for approval. Would you like to:\n\n- **Send**\n- **Edit**\n- **Discard**"
            st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
    # 3. Standard Query Routing
    else:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.chat_message("assistant"):
            with st.spinner("Processing agentic workflows..."):
                try:
                    response = process_agent_query(user_input)
                    st.markdown(response)
                except Exception:
                    response = "We couldn't process your request. Please try again."
                    st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()
