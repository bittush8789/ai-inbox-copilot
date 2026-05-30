import streamlit as st

def inject_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            /* Core Theme & Typography Reset */
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif !important;
                background-color: #0B1020 !important;
                color: #F8FAFC !important;
            }
            
            [data-testid="stAppViewContainer"] {
                background-color: #0B1020 !important;
            }

            [data-testid="stHeader"] {
                background-color: transparent !important;
            }

            /* Global Typography Color Fix for Markdown, Chat, Paragraphs, Lists */
            .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div,
            p, li, span, h1, h2, h3, h4, h5, h6 {
                color: #F8FAFC !important;
            }

            /* Container Spacing & Layout */
            .main .block-container {
                max-width: 1100px !important;
                padding-top: 2rem !important;
                padding-bottom: 6rem !important;
                margin: 0 auto !important;
                background-color: #0B1020 !important;
            }
            
            /* Hide Streamlit elements */
            [data-testid="stSidebar"] {
                display: none !important;
            }
            [data-testid="stSidebarCollapseButton"] {
                display: none !important;
            }
            
            /* Glassmorphic Top Nav Header */
            .glass-header {
                background: rgba(17, 24, 39, 0.75) !important;
                backdrop-filter: blur(16px) saturate(180%);
                -webkit-backdrop-filter: blur(16px) saturate(180%);
                border: 1px solid #1E293B !important;
                border-radius: 16px;
                padding: 1rem 1.5rem;
                margin-bottom: 2.5rem;
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
            }
            
            /* Premium Modern SaaS Cards */
            .premium-card {
                background: rgba(26, 35, 50, 0.6) !important;
                backdrop-filter: blur(8px);
                border: 1px solid #1E293B !important;
                border-radius: 16px !important;
                padding: 1.5rem !important;
                margin-bottom: 1.5rem !important;
                box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5) !important;
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
            }

            .premium-card:hover {
                transform: translateY(-2px);
                border-color: #7C3AED !important;
                box-shadow: 0 12px 35px -8px rgba(124, 58, 237, 0.15) !important;
            }
            
            /* Muted Text Classes */
            .muted-text, .premium-card .muted-text, .glass-header .muted-text {
                color: #94A3B8 !important;
            }

            .submuted-text, .premium-card .submuted-text {
                color: #64748B !important;
            }
            
            /* Custom headers & gradient text */
            .saas-title {
                background: linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 700;
                margin: 0;
                letter-spacing: -0.025em;
            }
            
            /* Custom Chat Timeline styling */
            [data-testid="stChatMessage"] {
                background-color: #111827 !important;
                border: 1px solid #1E293B !important;
                border-radius: 16px !important;
                padding: 1.2rem 1.5rem !important;
                margin-bottom: 1rem !important;
                box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.3) !important;
            }

            [data-testid="stChatMessage"] *, [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
                color: #F8FAFC !important;
            }
            
            /* Target Streamlit Buttons to look premium and aligned */
            div.stButton > button {
                background-color: #1A2332 !important;
                color: #F8FAFC !important;
                border: 1px solid #1E293B !important;
                border-radius: 12px !important;
                padding: 0.6rem 1.2rem !important;
                height: 48px !important;
                font-weight: 500 !important;
                font-size: 0.95rem !important;
                width: 100% !important;
                transition: all 0.2s ease-in-out !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
            }

            div.stButton > button:hover {
                border-color: #7C3AED !important;
                color: #FFFFFF !important;
                background-color: #1E293B !important;
                transform: translateY(-1px);
            }

            /* Primary Button overrides */
            div.stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%) !important;
                color: #FFFFFF !important;
                border: none !important;
                font-weight: 600 !important;
            }

            div.stButton > button[kind="primary"]:hover {
                background: linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%) !important;
                box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
            }
            
            /* Fixed Chat Input Bar at Bottom (Notion/ChatGPT style) */
            [data-testid="stChatInput"] {
                background-color: #111827 !important;
                border: 1px solid #1E293B !important;
                border-radius: 16px !important;
                padding: 0.5rem !important;
                box-shadow: 0 -10px 30px -10px rgba(0,0,0,0.5) !important;
            }
            
            [data-testid="stChatInput"] textarea {
                background-color: transparent !important;
                color: #F8FAFC !important;
                border: none !important;
                padding: 0.6rem 1rem !important;
                font-size: 0.95rem !important;
            }

            [data-testid="stChatInput"] button {
                background-color: #7C3AED !important;
                border-radius: 10px !important;
                color: #FFFFFF !important;
            }

            [data-testid="stChatInput"] button:hover {
                background-color: #8B5CF6 !important;
            }

            /* Badges & Alerts contrast colors */
            .p-badge-high {
                background-color: rgba(239, 68, 68, 0.15);
                color: #EF4444 !important;
                padding: 4px 10px;
                border-radius: 8px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
            }

            .p-badge-medium {
                background-color: rgba(245, 158, 11, 0.15);
                color: #F59E0B !important;
                padding: 4px 10px;
                border-radius: 8px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
            }

            .p-badge-low {
                background-color: rgba(34, 197, 94, 0.15);
                color: #22C55E !important;
                padding: 4px 10px;
                border-radius: 8px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
            }

            /* Dialogs glass overrides */
            div[data-testid="stDialog"] {
                background-color: #111827 !important;
                border: 1px solid #1E293B !important;
                border-radius: 20px !important;
            }
        </style>
    """, unsafe_allow_html=True)
