import streamlit as st

def inject_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
            
            /* Apply premium styling and backgrounds */
            html, body, [class*="css"] {
                font-family: 'Outfit', sans-serif;
                background-color: #0A0F1F !important;
                color: #FFFFFF !important;
            }
            
            [data-testid="stAppViewContainer"] {
                background-color: #0A0F1F !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }

            /* Center layout - restrict blockcontainer max width */
            .main .block-container {
                max-width: 900px !important;
                padding-top: 1rem !important;
                padding-bottom: 2rem !important;
                margin: 0 auto !important;
            }
            
            /* Hide Streamlit sidebars completely */
            [data-testid="stSidebar"] {
                display: none !important;
            }
            [data-testid="stSidebarCollapseButton"] {
                display: none !important;
            }
            
            /* Glassmorphic Top Nav Header */
            .glass-header {
                background: rgba(19, 26, 43, 0.7);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                padding: 0.75rem 1.25rem;
                margin-bottom: 1.5rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
            }
            
            /* Compact Cards & Details */
            .premium-card {
                background-color: #131A2B !important;
                border: 1px solid rgba(124, 92, 255, 0.1) !important;
                border-radius: 16px !important;
                padding: 1rem !important;
                margin-bottom: 1rem !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
            }

            .premium-card:hover {
                border-color: rgba(124, 92, 255, 0.3) !important;
            }
            
            .muted-text {
                color: #94A3B8 !important;
                font-size: 0.85rem;
            }

            /* Priority Pills */
            .p-badge-high {
                background-color: rgba(239, 68, 68, 0.15);
                color: #EF4444;
                padding: 2px 8px;
                border-radius: 8px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
            }

            .p-badge-medium {
                background-color: rgba(245, 158, 11, 0.15);
                color: #F59E0B;
                padding: 2px 8px;
                border-radius: 8px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
            }

            .p-badge-low {
                background-color: rgba(34, 197, 94, 0.15);
                color: #22C55E;
                padding: 2px 8px;
                border-radius: 8px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
            }

            /* Custom headers */
            .saas-title {
                background: linear-gradient(135deg, #7C5CFF 0%, #B885FF 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 700;
                margin: 0;
            }
            
            /* Custom Chat Bubbles */
            [data-testid="stChatMessage"] {
                background-color: #131A2B !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                border-radius: 16px !important;
                padding: 0.8rem 1.2rem !important;
                margin-bottom: 0.75rem !important;
            }
            
            /* Customize Chat Inputs */
            [data-testid="stChatInput"] textarea {
                background-color: #131A2B !important;
                color: #FFFFFF !important;
                border: 1px solid rgba(124, 92, 255, 0.2) !important;
                border-radius: 12px !important;
            }
            
            /* Suggestion Chips */
            .chip-container {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin-bottom: 1.5rem;
            }
        </style>
    """, unsafe_allow_html=True)
