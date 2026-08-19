import streamlit as st
import time
import os
from dotenv import load_dotenv
from tools.groq_utils import create_chat_completion, client


load_dotenv()

from agents.router import route_query
from pipelines.research_pipeline import run_research_pipeline
from workflows.graph_workflow import run_graph
from pipelines.stock_pipeline import (run_stock_pipeline,get_stock_chart,get_stock_metrics,get_news_sentiment)
from pipelines.code_pipeline import run_code_pipeline
from pipelines.job_pipeline import run_job_pipeline
from pipelines.flight_pipeline import run_flight_pipeline
from pipelines.image_pipeline import generate_image
from pipelines.general_pipeline import run_general_pipeline
from streamlit_folium import folium_static

try:
    from memory.rag_engine import (add_pdf_to_db, search_documents, get_stored_documents, clear_documents)
    doc_import_error = None
except Exception as e:
    add_pdf_to_db = lambda *args, **kwargs: "❌ Document feature unavailable"
    search_documents = lambda *args, **kwargs: []
    get_stored_documents = lambda *args, **kwargs: []
    clear_documents = lambda *args, **kwargs: "❌ Document feature unavailable"
    doc_import_error = str(e)

from memory.pins_db import init_db, add_pin, get_all_pins, delete_pin, get_pin
from memory.history_db import init_history_db, add_history, get_history, clear_history, get_domain_counts, DOMAIN_ICONS
# Page config
st.set_page_config(
    page_title="Multi-Agent AI System",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0d0d0d 0%, #1a1a2e 100%);
}
[data-testid="stHeader"] {
    background: transparent;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111111 0%, #0a0a0a 100%);
    border-right: 1px solid #2a2a2a;
}
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
    border: 1px solid #2a2a2a;
    color: #ccc;
    font-size: 0.78rem;
    text-align: left;
    padding: 8px 12px;
    border-radius: 8px;
    margin: 2px 0;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #222 0%, #2a2a2a 100%);
    border-color: #FF6B35;
    color: #fff;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
}
[data-testid="stSidebar"] .stButton > button:active {
    transform: translateY(0);
}

/* ── Agent cards row ── */
.agent-cards-row {
    display: flex;
    gap: 12px;
    padding: 16px 0;
    flex-wrap: wrap;
    justify-content: center;
}
.agent-card {
    background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    min-width: 110px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    position: relative;
    overflow: hidden;
}
.agent-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255, 107, 53, 0.1) 0%, transparent 100%);
    opacity: 0;
    transition: opacity 0.3s;
}
.agent-card:hover {
    border-color: #FF6B35;
    background: linear-gradient(135deg, #1f1a15 0%, #2a2520 100%);
    transform: translateY(-4px) scale(1.05);
    box-shadow: 0 8px 20px rgba(255, 107, 53, 0.4);
}
.agent-card:hover::before {
    opacity: 1;
}
.agent-card.active {
    border-color: #FF6B35;
    background: linear-gradient(135deg, #1f1a15 0%, #2a2520 100%);
    box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.3), 0 4px 12px rgba(255, 107, 53, 0.3);
}
.agent-card-icon {
    font-size: 20px;
    transition: transform 0.3s;
}
.agent-card:hover .agent-card-icon {
    transform: scale(1.2) rotate(5deg);
}
.agent-card-label {
    font-size: 13px;
    font-weight: 600;
    color: #eee;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.agent-card-sub {
    font-size: 10px;
    color: #888;
    font-weight: 500;
}

/* ── Chat messages ── */
.user-msg {
    background: linear-gradient(135deg, #1e3a5f 0%, #2a4a7f 100%);
    padding: 14px 18px;
    border-radius: 20px 20px 6px 20px;
    color: white;
    margin: 10px 0;
    max-width: 75%;
    margin-left: auto;
    font-size: 14px;
    box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
    animation: slideInRight 0.4s ease-out;
}
.ai-msg {
    background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
    padding: 14px 18px;
    border-radius: 6px 20px 20px 20px;
    color: #e0e0e0;
    margin: 10px 0;
    max-width: 80%;
    border: 1px solid #2a2a2a;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    animation: slideInLeft 0.4s ease-out;
}
@keyframes slideInRight {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}
.msg-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}
.domain-badge {
    font-size: 11px;
    background: linear-gradient(135deg, #1f2a1f 0%, #2a3a2a 100%);
    color: #4caf50;
    border: 1px solid #4caf50;
    border-radius: 6px;
    padding: 3px 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.score-badge {
    font-size: 11px;
    background: linear-gradient(135deg, #1a1f2a 0%, #2a2f3a 100%);
    color: #64b5f6;
    border: 1px solid #64b5f6;
    border-radius: 6px;
    padding: 3px 10px;
    font-weight: 600;
}

/* ── Execution log ── */
.exec-log {
    background: linear-gradient(135deg, #111 0%, #1a1a1a 100%);
    border: 1px solid #222;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 12px;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
}
.log-row {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    color: #888;
    padding: 4px 0;
    transition: color 0.3s;
}
.log-row:hover {
    color: #aaa;
}
.log-dot-done   { 
    width:8px;height:8px;border-radius:50%;background:linear-gradient(135deg,#4caf50,#66bb6a);
    flex-shrink:0;
    box-shadow: 0 0 8px rgba(76, 175, 80, 0.5);
}
.log-dot-active { 
    width:8px;height:8px;border-radius:50%;background:linear-gradient(135deg,#FF6B35,#ff8c5a);
    flex-shrink:0;
    box-shadow: 0 0 8px rgba(255, 107, 53, 0.5);
    animation: pulse 1.5s infinite;
}
.log-dot-wait   { 
    width:8px;height:8px;border-radius:50%;background:#333;
    flex-shrink:0;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
.log-time { 
    margin-left: auto; 
    font-size: 11px; 
    color: #666;
    font-family: monospace;
}

/* ── Input bar ── */
[data-testid="stChatInput"] > div {
    border-radius: 28px !important;
    border: 2px solid #333 !important;
    background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%) !important;
    padding: 6px 12px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    transition: all 0.3s;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #FF6B35 !important;
    box-shadow: 0 4px 20px rgba(255, 107, 53, 0.3);
}
[data-testid="stChatInput"] textarea {
    color: #eee !important;
    font-size: 14px !important;
    background: transparent !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #666 !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    transition: transform 0.3s;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
}

/* ── Info/success boxes ── */
[data-testid="stAlert"] {
    border-radius: 12px;
    border: 1px solid #333;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    transition: all 0.3s;
}
[data-testid="stExpander"]:hover {
    border-color: #3a3a3a;
}

/* ── Title ── */
h1 { 
    color: #fff !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    font-weight: 800;
}
h2 { 
    color: #eee !important;
    font-weight: 700;
}
h3 { 
    color: #ddd !important;
    font-weight: 600;
}
p  { 
    color: #ccc !important;
    line-height: 1.7;
}

/* ── Scrollbar ── */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-track {
    background: #111;
}
::-webkit-scrollbar-thumb {
    background: #333;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #444;
}
</style>
""", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pinned" not in st.session_state:
    st.session_state.pinned = []
if "view_pin" not in st.session_state:
    st.session_state.view_pin = None
if "show_all_pins" not in st.session_state:
    st.session_state.show_all_pins = False
if "selected_query" not in st.session_state:
    st.session_state.selected_query = None
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = "research"

# Style history buttons to look like dark cards
st.markdown("""
<style>
[data-testid="stSidebar"] .stButton > button {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    color: #ddd;
    font-size: 0.8rem;
    text-align: left;
    padding: 6px 10px;
    border-radius: 6px;
    margin: 1px 0;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #252545;
    border-color: #FF6B35;
    color: #fff;
}
</style>
""", unsafe_allow_html=True)

# Initialize pins DB and load persisted pins
init_db()
init_history_db()
st.session_state.pinned = get_all_pins()

# Header
st.title("🤖 Multi-Agent AI System")
st.markdown("*Powered by Groq + Llama 3.3 — Built by Nida Ashrafi*")
st.divider()

# Agent cards row
col1, col2, col3, col4 = st.columns(4)
col5, col6, col7 = st.columns(3)

agents = [
    {"id": "research", "icon": "🔬", "label": "Research", "sub": "100% acc"},
    {"id": "stock", "icon": "�", "label": "Stock", "sub": "Live data"},
    {"id": "code", "icon": "💻", "label": "Code", "sub": "100% acc"},
    {"id": "job", "icon": "💼", "label": "Job", "sub": "100% acc"},
    {"id": "flight", "icon": "✈️", "label": "Flight", "sub": "Live map"},
    {"id": "image", "icon": "🎨", "label": "Image", "sub": "AI gen"},
    {"id": "general", "icon": "💬", "label": "General", "sub": "Streaming"}
]

cols = [col1, col2, col3, col4, col5, col6, col7]

for idx, agent in enumerate(agents):
    with cols[idx]:
        is_active = st.session_state.selected_agent == agent["id"]
        active_class = "active" if is_active else ""
        card_style = f"""
        <div class="agent-card {active_class}" style="cursor: pointer;">
            <span class="agent-card-icon">{agent["icon"]}</span>
            <div>
                <div class="agent-card-label">{agent["label"]}</div>
                <div class="agent-card-sub">{agent["sub"]}</div>
            </div>
        </div>
        """
        st.markdown(card_style, unsafe_allow_html=True)
        if st.button("", key=f"agent_{agent['id']}", use_container_width=True):
            st.session_state.selected_agent = agent["id"]
            st.rerun()


def stream_text_response(text: str, placeholder, delay: float = 0.02):
    """Render output progressively for non-streaming pipeline results."""
    full_text = ""
    for chunk in text.split(" "):
        full_text += chunk + " "
        placeholder.markdown(full_text + "▌")
        time.sleep(delay)
    placeholder.markdown(full_text)
    return full_text

# Sidebar — Mission Control
with st.sidebar:

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        border-radius: 16px;
        padding: 20px 18px 16px;
        margin-bottom: 12px;
        border: 2px solid #444;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute;
            top: -50%;
            right: -50%;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle, rgba(255,107,53,0.1) 0%, transparent 70%);
            pointer-events: none;
        "></div>
        <div style="font-size:1.4rem;font-weight:900;color:#fff;letter-spacing:1.5px;text-shadow:0 2px 4px rgba(0,0,0,0.5)">
            🕹️ MISSION CONTROL
        </div>
        <div style="font-size:0.85rem;color:#bbb;margin-top:4px;font-weight:500">
            Multi-Agent AI System
        </div>
        <div style="
            margin-top: 8px;
            padding: 6px 12px;
            background: rgba(255,107,53,0.15);
            border-radius: 6px;
            font-size: 0.75rem;
            color: #FF6B35;
            font-weight: 600;
            border: 1px solid rgba(255,107,53,0.3);
        ">
            ⚡ Powered by Groq + Llama 3.3
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── New Chat button ──────────────────────────────────────────────────────
    if st.button("✏️ New Chat", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.selected_query = None
        st.session_state.view_pin = None
        st.session_state.show_all_pins = False
        st.rerun()

    # ── Chat History ─────────────────────────────────────────────────────────
    history = get_history()

    if history:
        from datetime import datetime, date

        today     = date.today()
        yesterday = date.fromordinal(today.toordinal() - 1)

        buckets = {"📅 TODAY": [], "📅 YESTERDAY": [], "📅 EARLIER": []}
        for h in history:
            try:
                hdate = datetime.strptime(h["timestamp"], "%Y-%m-%d %H:%M").date()
            except Exception:
                hdate = today
            if hdate == today:
                buckets["📅 TODAY"].append(h)
            elif hdate == yesterday:
                buckets["📅 YESTERDAY"].append(h)
            else:
                buckets["📅 EARLIER"].append(h)

        for bucket_label, items in buckets.items():
            if not items:
                continue
            st.markdown(
                f"<div style='color:#FF6B35;font-size:0.8rem;font-weight:800;"
                f"letter-spacing:1.5px;margin:12px 0 6px;padding-left:4px;border-left:3px solid #FF6B35'>{bucket_label}</div>",
                unsafe_allow_html=True
            )
            for h in items[:8]:
                icon  = DOMAIN_ICONS.get(h["domain"], "💬")
                htime = h["timestamp"][11:16]
                title = h["title"][:28] + ("…" if len(h["title"]) > 28 else "")
                label = f"{icon} {htime}  {title}"
                if st.button(label, key=f"hist_{h['id']}", use_container_width=True):
                    st.session_state.selected_query = h["query"]
                    st.rerun()

        # ── Most Used ────────────────────────────────────────────────────────
        counts = get_domain_counts()
        if counts:
            st.markdown(
                "<div style='color:#FF6B35;font-size:0.8rem;font-weight:800;"
                "letter-spacing:1.5px;margin:12px 0 6px;padding-left:4px;border-left:3px solid #FF6B35'>🔥 MOST USED</div>",
                unsafe_allow_html=True
            )
            for domain_key, cnt in list(counts.items())[:5]:
                icon  = DOMAIN_ICONS.get(domain_key, "💬")
                label = domain_key.capitalize()
                bar_w = min(100, int(cnt / max(counts.values()) * 100))
                st.markdown(f"""
                <div style='margin:4px 0'>
                    <div style='display:flex;justify-content:space-between;
                                font-size:0.85rem;color:#eee;margin-bottom:4px;font-weight:500'>
                        <span>{icon} {label}</span>
                        <span style='color:#FF6B35;font-weight:600'>{cnt}x</span>
                    </div>
                    <div style='background:linear-gradient(90deg,#1a1a2e,#252525);border-radius:6px;height:8px;border:1px solid #333'>
                        <div style='background:linear-gradient(90deg,#FF6B35,#f7c948);
                                    width:{bar_w}%;height:8px;border-radius:6px;box-shadow:0 0 8px rgba(255,107,53,0.5)'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin:8px 0'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear History", use_container_width=True):
            clear_history()
            st.rerun()
    else:
        st.markdown(
            "<div style='color:#666;font-size:0.85rem;padding:12px 0'>"
            "No queries yet. Start chatting!</div>",
            unsafe_allow_html=True
        )

    st.divider()

    # ── Pinned Messages ──────────────────────────────────────────────────────
    pins = get_all_pins()
    st.markdown("### 📌 Pinned Messages")
    if pins:
        for pin in pins:
            with st.expander(f"📌 {pin['title']}"):
                st.markdown(f"**Timestamp:** {pin.get('timestamp')}  \n\n**User:** {pin.get('user_prompt')}\n\n**AI:** {pin.get('content')[:400]}...")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📖 View Full", key=f"view_{pin['id']}"):
                        st.session_state.view_pin = pin
                        st.session_state.show_all_pins = False
                        st.rerun()
                with col2:
                    if st.button("🗑️ Unpin", key=f"unpin_{pin['id']}"):
                        delete_pin(pin['id'])
                        st.session_state.pinned = get_all_pins()
                        st.success("Unpinned")
                        st.rerun()
    else:
        st.caption("No pinned messages yet.")
        if st.button("Open Pinned Messages"):
            st.session_state.show_all_pins = True

    st.divider()

    # ── About ────────────────────────────────────────────────────────────────
    st.markdown("### 📌 About")
    st.markdown("""
    This system uses multiple AI agents 
    to handle different types of queries.
    
    **Supported Domains:**
    - 🔬 Research & Reports
    - 📈 Stock Analysis
    - 💻 Code Review
    - 💼 Job Applications
    - ✈️ Flight Tracking
    - 💬 General Q&A
    """)

    st.divider()
    st.markdown("### 💡 Example Queries")
    st.markdown("""
    - *What are latest advancements in LLMs?*
    - *Analyse AAPL stock for me*
    - *Review this Python code: ...*
    - *Help me apply for ML Engineer job*
    - *Track flight AI102*
    - *Who invented the internet?*
    """)

    st.divider()
    st.markdown("### 📚 Document Upload")
    st.markdown("Upload PDFs to chat with your documents!")

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        help="Upload research papers, notes, or any PDF"
    )

    if uploaded_file:
        if st.button("📥 Add to Knowledge Base"):
            with st.spinner("Processing PDF..."):
                result = add_pdf_to_db(
                    uploaded_file,
                    uploaded_file.name
                )
            st.success(result)

    stored = get_stored_documents()
    if stored:
        st.divider()
        st.markdown("**📄 Stored Documents:**")
        for doc in stored:
            st.markdown(f"- {doc}")
        if st.button("🗑️ Clear All Documents"):
            result = clear_documents()
            st.success(result)
            st.rerun()

    st.divider()
    st.markdown("**Built with:**")
    st.markdown("🦙 Llama 3.3 70B")
    st.markdown("⚡ Groq API")
    st.markdown("🐍 Python")
    st.markdown("✈️ Aviationstack")
    st.markdown("🧠 ChromaDB RAG")

# Domain badge colors
domain_colors = {
    "research": "🔬 RESEARCH",
    "stock": "📈 STOCK",
    "code": "💻 CODE",
    "job": "💼 JOB",
    "flight": "✈️ FLIGHT",
    "image": "🎨 IMAGE",
    "general": "💬 GENERAL"
}

# Display selected pinned conversation (if any)
if st.session_state.view_pin:
    pin = st.session_state.view_pin
    st.header(f"📌 {pin.get('title')}")
    st.markdown(f"**Timestamp:** {pin.get('timestamp')}  \n\n**User:** {pin.get('user_prompt')}\n\n**AI:** {pin.get('content')}")
    if st.button("🗑️ Unpin (remove)", key=f"view_unpin_{pin.get('id')}"):
        delete_pin(pin.get('id'))
        st.session_state.view_pin = None
        st.session_state.pinned = get_all_pins()
        st.success("Unpinned")
        st.rerun()

# Show all pinned messages in main area when requested
if st.session_state.show_all_pins:
    st.header("📌 All Pinned Messages")
    pins = get_all_pins()
    if not pins:
        st.info("No pinned messages yet.")
    else:
        for pin in pins:
            with st.expander(f"📌 {pin['title']} - {pin.get('timestamp')}"):
                st.markdown(f"**User:** {pin.get('user_prompt')}\n\n**AI:** {pin.get('content')}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📖 View Full", key=f"main_view_{pin['id']}"):
                        st.session_state.view_pin = pin
                        st.session_state.show_all_pins = False
                        st.rerun()
                with col2:
                    if st.button("🗑️ Unpin", key=f"main_unpin_{pin['id']}"):
                        delete_pin(pin['id'])
                        st.session_state.pinned = get_all_pins()
                        st.success("Unpinned")
                        st.rerun()
    if st.button("Close Pinned Messages"):
        st.session_state.show_all_pins = False

# Display chat history
for idx, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        col1, col2 = st.columns([1, 3])
        with col2:
            # Show saved map if exists
            map_key = f"map_{idx}"
            if map_key in st.session_state:
                st.components.v1.html(
                    st.session_state[map_key],
                    height=500
                )
            st.markdown(f"""
            <div class="user-msg">
            🧑 {message['content']}
            </div>
            """, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            mtype = message.get("type")
            if mtype == "image":
                st.markdown(f"""
                <div class="ai-msg">
                <div class="msg-header">
                    <span class="domain-badge">🎨 IMAGE</span>
                    <span class="score-badge">AI GENERATED</span>
                </div>
                <div style="margin-bottom: 8px;">🤖 Generated image for: {message['original_query']}</div>
                <div style="margin-bottom: 8px;"><strong>Enhanced Prompt:</strong> {message['enhanced_prompt']}</div>
                </div>
                """, unsafe_allow_html=True)
                st.image(
                    message["image_url"],
                    caption=message["enhanced_prompt"],
                    width=700
                )
                st.caption(f"Generated: {message['generated_at']}")
            elif mtype == "stock":
                st.markdown(f"""
                <div class="ai-msg">
                <div class="msg-header">
                    <span class="domain-badge">� STOCK</span>
                    <span class="score-badge">LIVE DATA</span>
                </div>
                <div style="margin-bottom: 12px;"><strong>{message.get('metrics', {}).get('name', message.get('symbol'))}</strong></div>
                </div>
                """, unsafe_allow_html=True)
                cols = st.columns(4)
                with cols[0]:
                    st.metric("💰 Price", f"${message.get('metrics', {}).get('current_price')}", f"{message.get('metrics', {}).get('change')} ({message.get('metrics', {}).get('change_pct')}%)")
                with cols[1]:
                    st.metric("📈 52W High", f"${message.get('metrics', {}).get('52w_high')}")
                with cols[2]:
                    st.metric("📉 52W Low", f"${message.get('metrics', {}).get('52w_low')}")
                with cols[3]:
                    st.metric("📊 P/E Ratio", message.get('metrics', {}).get('pe_ratio'))

                st.divider()
                try:
                    chart = get_stock_chart(message.get('symbol'))
                except Exception as e:
                    print('Chart render error:', e)
                    chart = None

                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                else:
                    st.warning('Chart not available')
            else:
                domain = message.get("domain", "general")
                domain_badge = domain_colors.get(domain, "💬 GENERAL")
                st.markdown(f"""
                <div class="ai-msg">
                <div class="msg-header">
                    <span class="domain-badge">{domain_badge}</span>
                    <span class="score-badge">AI RESPONSE</span>
                </div>
                <div style="white-space: pre-wrap; overflow-wrap: anywhere;">
                {message['content']}
                </div>
                </div>
                """, unsafe_allow_html=True)

        # Pin button on the right column
        with col2:
            if st.button(
                "📌 Pin",
                key=f"pin_{idx}",
                help="Pin this response"
            ):
                title = "Pinned Response"
                if idx > 0:
                    prev = st.session_state.messages[idx-1]
                    title = prev.get('content','')[:40] + "..."

                already_pinned = any(
                    p.get('content') == message.get('content')
                    for p in st.session_state.pinned
                )

                if not already_pinned:
                    user_prompt = prev.get('content','') if idx > 0 else ""
                    add_pin(user_prompt, message.get('content',''), title=title)
                    st.session_state.pinned = get_all_pins()
                    st.success("📌 Pinned!")
                    st.rerun()
                else:
                    st.warning("Already pinned!")

# User input area with enhanced features
input_container = st.container()

with input_container:
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col1:
        # Quick action buttons
        if st.button("🔄", help="Clear input", use_container_width=True):
            st.session_state.clear_input = True
    
    with col2:
        # Enhanced chat input
        user_input = st.chat_input(
            placeholder=f"Ask {st.session_state.selected_agent.capitalize()} agent anything..."
        )
    
    with col3:
        # Agent selector indicator
        agent_icons = {
            "research": "🔬",
            "stock": "📈", 
            "code": "💻",
            "job": "💼",
            "flight": "✈️",
            "image": "🎨",
            "general": "💬"
        }
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 8px;
            background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
            border: 1px solid #2a2a2a;
            border-radius: 8px;
            font-size: 24px;
        ">
        {agent_icons.get(st.session_state.selected_agent, "💬")}
        </div>
        """, unsafe_allow_html=True)

# If a history item was clicked, use it as the query
if st.session_state.selected_query and not user_input:
    user_input = st.session_state.selected_query
    st.session_state.selected_query = None

if user_input:

    # Show user message
    col1, col2 = st.columns([1, 3])
    with col2:
        st.markdown(f"""
        <div class="user-msg">
        🧑 {user_input}
        </div>
        """, unsafe_allow_html=True)
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    col1, col2 = st.columns([3, 1])
    with col1:

        # Progress container
        progress_container = st.container()
        
        # Step 1 - Route
        with progress_container:
            st.markdown("""
            <div class="exec-log">
                <div class="log-row">
                    <div class="log-dot-active"></div>
                    <span>🔀 Router Agent analyzing query...</span>
                    <span class="log-time">Step 1/3</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        result = route_query(user_input)
        domain = result["domain"]

        # Save to persistent history
        add_history(domain, user_input)

        with progress_container:
            st.markdown("""
            <div class="exec-log">
                <div class="log-row">
                    <div class="log-dot-done"></div>
                    <span>✅ Router Agent completed</span>
                    <span class="log-time">Done</span>
                </div>
                <div class="log-row">
                    <div class="log-dot-active"></div>
                    <span>🚀 Running {domain} pipeline...</span>
                    <span class="log-time">Step 2/3</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        badge = domain_colors.get(domain, "💬 GENERAL")
        st.info(f"**Domain Detected:** {badge}")

        # Step 2 - Run pipeline
        if domain == "general":

            # Check if documents exist in RAG
            stored_docs = get_stored_documents()

            if stored_docs:
                # RAG mode - search documents first
                st.info("🧠 Searching your documents...")
                relevant_chunks = search_documents(user_input)

                if relevant_chunks:
                    context = "\n\n".join([
                        f"From {chunk['source']}:\n{chunk['content']}"
                        for chunk in relevant_chunks
                    ])

                    system_prompt = f"""You are a helpful AI assistant.
                    Answer clearly and in detail. Use markdown.
                    LANGUAGE RULE: If user writes in pure English
                    or mixed English (like 'Thank u', 'ok', 'thanks'),
                    ALWAYS respond in English.
                    Only respond in another language if user writes
                    FULLY in that language like Hindi, Tamil, Japanese.

                    DOCUMENT CONTEXT:
                    {context}
                    """
                    st.success(f"📄 Found relevant content from {len(relevant_chunks)} chunks!")
                else:
                    system_prompt = """You are a helpful AI assistant.
                    Answer clearly and in detail.
                    Use markdown formatting.

                    IMPORTANT: Always detect the language
                    of the user's message and respond in
                    that SAME language.
                    If user writes in Hindi, respond in Hindi.
                    If user writes in Japanese, respond in Japanese.
                    If user writes in Tamil, respond in Tamil.
                    Never switch languages unless user asks."""
            else:
                system_prompt = """You are a helpful AI assistant.
                Answer clearly and in detail.
                Use markdown formatting.
                Add examples where needed.

                IMPORTANT: Always detect the language
                of the user's message and respond in
                that SAME language.
                If user writes in Hindi, respond in Hindi.
                If user writes in Japanese, respond in Japanese.
                If user writes in Tamil, respond in Tamil.
                Never switch languages unless user asks."""

            # STREAMING
            st.subheader("💬 Answer")
            stream_placeholder = st.empty()
            full_response = ""

            try:
                stream = create_chat_completion(
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_input
                        }
                    ],
                    stream=True
                )

                # Debug: log stream object details to help diagnose intermittent failures
                try:
                    print("Stream object type:", type(stream))
                    print("Stream repr (truncated):", repr(stream)[:500])
                except Exception as _:
                    pass

                for chunk in stream:
                    try:
                        choices = getattr(chunk, "choices", None)
                        if not choices:
                            continue
                        delta = getattr(choices[0], "delta", None)
                        content = None
                        if delta is not None:
                            content = getattr(delta, "content", None)

                        if content:
                            full_response += content
                            stream_placeholder.markdown(full_response + "▌")
                            time.sleep(0.01)
                    except Exception as e:
                        print("Stream chunk error:", e)
                        continue

                stream_placeholder.markdown(full_response)
                output = full_response
            except Exception as e:
                # Streaming failed — fallback to non-streaming call
                import traceback
                print("Streaming failed, falling back to non-streaming call:", type(e).__name__, e)
                traceback.print_exc()
                try:
                    fallback = create_chat_completion(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_input}
                        ],
                        stream=False
                    )

                    # Robustly extract content from different possible response shapes
                    content = None
                    try:
                        content = getattr(fallback.choices[0].message, "content", None)
                    except Exception:
                        try:
                            content = fallback.choices[0]["message"]["content"]
                        except Exception:
                            try:
                                content = getattr(fallback.choices[0], "text", None)
                            except Exception:
                                content = None

                    if not content:
                        # As a last resort, stringify the fallback for logs
                        try:
                            content = str(fallback)
                        except Exception:
                            content = ""

                    output = content
                    stream_placeholder.markdown(output)
                except Exception as e2:
                    print("Fallback non-streaming error:", type(e2).__name__, e2)
                    import traceback as _tb
                    _tb.print_exc()
                    output = "Sorry, an error occurred while generating the response."

        elif domain == "image":
            with st.spinner("🎨 Generating your image..."):
                result = generate_image(user_input)

            st.subheader("🎨 Image Generation Result")

            # Show prompts
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Your Request:**\n{result['original_query']}")
            with col2:
                st.success(f"**Enhanced Prompt:**\n{result['enhanced_prompt']}")

            st.divider()

            # Show image
            with st.spinner("🖼️ Loading image..."):
                st.image(
                    result["image_url"],
                    caption=result["enhanced_prompt"],
                    width=700
                )

            # Download button
            st.markdown(f"""
            <a href="{result['image_url']}" target="_blank">
                <button style="
                    background: #FF6B35;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 16px;
                ">
                📥 Open Full Image
                </button>
            </a>
            """, unsafe_allow_html=True)

            st.caption(f"Generated: {result['generated_at']}")
            output = f"Generated image for: {result['original_query']}"
            assistant_message = {
                "role": "assistant",
                "content": output,
                "type": "image",
                "original_query": result["original_query"],
                "enhanced_prompt": result["enhanced_prompt"],
                "image_url": result["image_url"],
                "generated_at": result["generated_at"]
            }

        elif domain == "flight":
            with st.spinner("✈️ Fetching live flight data..."):
                report, flight_map, enriched = run_flight_pipeline(user_input)

            if enriched:
                # ── Status badge ───────────────────────────────────────────
                status_raw = enriched["status"].lower()
                status_map = {
                    "active":    ("🟢", "IN AIR",    "#00c853"),
                    "scheduled": ("🔵", "SCHEDULED", "#0288d1"),
                    "landed":    ("🟡", "LANDED",    "#f9a825"),
                    "cancelled": ("🔴", "CANCELLED", "#d32f2f"),
                    "diverted":  ("🟣", "DIVERTED",  "#7b1fa2"),
                    "delayed":   ("🟠", "DELAYED",   "#e65100"),
                }
                s_emoji, s_label, s_color = status_map.get(
                    status_raw, ("⚪", "UNKNOWN", "#555555")
                )

                st.markdown(f"""
                <div style="background:{s_color}22;border-left:5px solid {s_color};
                            padding:14px 18px;border-radius:8px;margin-bottom:12px;">
                    <span style="font-size:1.4rem;font-weight:700;color:{s_color}">
                        {s_emoji} {enriched['flight_number']} — {s_label}
                    </span>
                    &nbsp;&nbsp;
                    <span style="color:#aaa;font-size:0.95rem">
                        {enriched['airline']}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                # ── AI Summary ─────────────────────────────────────────────
                st.info(f"🤖 **AI Summary:** {enriched['ai_summary']}")

                # ── Progress bar ───────────────────────────────────────────
                prog = enriched["progress"]
                if prog.get("available"):
                    st.markdown("**✈️ Flight Progress**")
                    st.progress(int(prog["pct"]) / 100,
                                text=f"{prog['pct']}% complete — "
                                     f"{prog['completed_km']} km done, "
                                     f"{prog['remaining_km']} km remaining "
                                     f"(total {prog['total_km']} km)")
                elif status_raw == "scheduled":
                    dep_sched = enriched["departure"].get("scheduled", "")
                    st.markdown(f"**✈️ Flight Progress** — 📅 Scheduled to depart at `{dep_sched[:16] if dep_sched else 'N/A'}` UTC")
                    st.progress(0.0, text="Not yet departed")

                # ── Delay + Countdown row ──────────────────────────────────
                dc1, dc2, dc3 = st.columns(3)
                with dc1:
                    dep_d = enriched["dep_delay"]
                    if dep_d is not None:
                        color = "🔴" if dep_d > 0 else "🟢"
                        st.metric("🛫 Dep. Delay",
                                  f"{color} {abs(dep_d)} min",
                                  delta=f"{'Late' if dep_d > 0 else 'Early'}")
                    else:
                        st.metric("🛫 Dep. Delay", "On Schedule" if status_raw == "scheduled" else "Not Available")
                with dc2:
                    arr_d = enriched["arr_delay"]
                    if arr_d is not None:
                        color = "🔴" if arr_d > 0 else "🟢"
                        st.metric("🛬 Arr. Delay",
                                  f"{color} {abs(arr_d)} min",
                                  delta=f"{'Late' if arr_d > 0 else 'Early'}")
                    else:
                        st.metric("🛬 Arr. Delay", "On Schedule" if status_raw == "scheduled" else "Not Available")
                with dc3:
                    cd = enriched["countdown"]
                    if cd.get("available") and not cd.get("landed_or_past"):
                        st.metric("⏱️ ETA",
                                  f"{cd['hours']}h {cd['minutes']}m remaining")
                    elif cd.get("landed_or_past"):
                        st.metric("⏱️ ETA", "🟡 Arrived / Past ETA")
                    elif status_raw == "scheduled":
                        arr_sched = enriched["arrival"].get("scheduled", "")
                        st.metric("⏱️ ETA", f"Scheduled {arr_sched[:10] if arr_sched else 'N/A'}")
                    else:
                        st.metric("⏱️ ETA", "Not Available")

                st.divider()

                # ── Expandable sections ────────────────────────────────────

                with st.expander("🛫 Departure Airport Details", expanded=True):
                    d = enriched["departure"]
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Airport:** {d['name']}")
                    c1.markdown(f"**IATA:** {d['iata']}  |  **ICAO:** {d['icao']}")
                    c2.markdown(f"**Terminal:** {d['terminal']}")
                    c2.markdown(f"**Gate:** {d['gate']}")
                    c3.markdown(f"**Timezone:** {d['timezone']}")
                    st.markdown(
                        f"**Scheduled:** {d['scheduled']}  &nbsp;|&nbsp; "
                        f"**Estimated:** {d['estimated']}  &nbsp;|&nbsp; "
                        f"**Actual:** {d['actual']}"
                    )

                with st.expander("🛬 Arrival Airport Details", expanded=True):
                    a = enriched["arrival"]
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Airport:** {a['name']}")
                    c1.markdown(f"**IATA:** {a['iata']}  |  **ICAO:** {a['icao']}")
                    c2.markdown(f"**Terminal:** {a['terminal']}")
                    c2.markdown(f"**Gate:** {a['gate']}")
                    c3.markdown(f"**Timezone:** {a['timezone']}")
                    st.markdown(
                        f"**Scheduled:** {a['scheduled']}  &nbsp;|&nbsp; "
                        f"**Estimated:** {a['estimated']}  &nbsp;|&nbsp; "
                        f"**Actual:** {a['actual']}"
                    )

                with st.expander("🛩️ Aircraft Details"):
                    ac = enriched["aircraft"]
                    # Only show fields that have real data
                    available_fields = {
                        "Registration": ac["registration"],
                        "IATA Type": ac["iata"],
                        "ICAO Type": ac["icao"],
                        "ICAO24": ac["icao24"],
                    }
                    real_fields = {k: v for k, v in available_fields.items() if v not in (None, "Not Available", "")}
                    if real_fields:
                        cols = st.columns(len(real_fields))
                        for col, (label, value) in zip(cols, real_fields.items()):
                            col.metric(label, value)
                        missing = [k for k in available_fields if k not in real_fields]
                        if missing:
                            st.caption(f"Not available from API: {', '.join(missing)}")
                    else:
                        st.info("Aircraft details not provided by the API for this flight.")

                with st.expander("📍 Live Position"):
                    lv = enriched["live"]
                    if lv:
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Latitude", lv.get("latitude", "N/A"))
                        c2.metric("Longitude", lv.get("longitude", "N/A"))
                        c3.metric("Altitude (m)", lv.get("altitude", "N/A"))
                        c4.metric("Speed (km/h)", lv.get("speed", "N/A"))
                    else:
                        status_raw = enriched["status"].lower()
                        if status_raw == "scheduled":
                            st.info("📅 Flight hasn't departed yet — live position will appear once airborne.")
                        elif status_raw == "landed":
                            st.info("🛬 Flight has already landed — no live position available.")
                        elif status_raw == "cancelled":
                            st.warning("❌ Flight was cancelled — no live position available.")
                        else:
                            st.info("📡 Live position not available from tracking network right now.")

                with st.expander("🌤️ Weather at Airports"):
                    wc1, wc2 = st.columns(2)
                    with wc1:
                        st.markdown(f"**🛫 {enriched['departure']['iata']} — Departure Weather**")
                        dw = enriched["dep_weather"]
                        if dw.get("available"):
                            st.markdown(f"🌡️ **{dw['temp_c']}°C**")
                            st.markdown(f"☁️ {dw['condition']}")
                            st.markdown(f"💧 Humidity: {dw['humidity_pct']}%  |  💨 Wind: {dw['wind_kmh']} km/h")
                            st.markdown(f"👁️ Visibility: {dw['visibility_km']} km")
                        else:
                            reason = dw.get("reason", "")
                            st.caption(f"Weather unavailable — {reason}" if reason else "Weather data not available.")
                    with wc2:
                        st.markdown(f"**🛬 {enriched['arrival']['iata']} — Arrival Weather**")
                        aw = enriched["arr_weather"]
                        if aw.get("available"):
                            st.markdown(f"🌡️ **{aw['temp_c']}°C** (feels {aw.get('feels_like_c', aw['temp_c'])}°C)")
                            st.markdown(f"☁️ {aw['condition']}")
                            st.markdown(f"💧 Humidity: {aw['humidity_pct']}%  |  💨 Wind: {aw['wind_kmh']} km/h")
                            st.markdown(f"👁️ Visibility: {aw['visibility_km']} km")
                        else:
                            reason = aw.get("reason", "")
                            st.caption(f"Weather unavailable — {reason}" if reason else "Weather data not available.")
                            if "OPENWEATHER_API_KEY" in reason:
                                st.caption("Add `OPENWEATHER_API_KEY` to your `.env` to enable weather.")

            else:
                # Fallback: AI-only mode (no live data)
                st.subheader("✈️ Flight Report")
                flight_placeholder = st.empty()
                stream_text_response(report, flight_placeholder)

            if flight_map:
                st.divider()
                st.subheader("🗺️ Live Flight Map")
                folium_static(flight_map, width=700, height=500)
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("🔄 Refresh Map"):
                        st.rerun()
                with col2:
                    st.caption("Click refresh to get latest position")

            # Save map as HTML in session
            if flight_map:
                import io
                map_html = flight_map._repr_html_()
                st.session_state[f"map_{len(st.session_state.messages)}"] = map_html
            output = report

        elif domain == "research":

            # LangGraph execution with live node updates
            st.subheader("🔗 LangGraph Execution")
            node_placeholder = st.empty()

            with st.spinner("🔗 LangGraph pipeline running..."):
                graph_result = run_graph(user_input)

            # Show execution log
            log_text = ""
            for log in graph_result["execution_log"]:
                log_text += f"{log['status']} **{log['node']}**\n"
                log_text += f"   → {log['detail']}\n\n"
                node_placeholder.markdown(log_text)

            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "⭐ Quality Score",
                    f"{graph_result['quality_score']}/100"
                )
            with col2:
                st.metric(
                    "🔄 Retries",
                    graph_result['retry_count']
                )
            with col3:
                st.metric(
                    "📍 Nodes Executed",
                    len(graph_result['execution_log'])
                )

            st.divider()

            # Final report
            # Final report — STREAMING!
            st.subheader("📄 Research Report")
            stream_placeholder = st.empty()
            full_text = ""

            # Stream word by word
            words = graph_result["written_report"].split(" ")
            for word in words:
                full_text += word + " "
                stream_placeholder.markdown(full_text + "▌")
                time.sleep(0.02)
            stream_placeholder.markdown(full_text)
            output = graph_result["final_output"]

        elif domain == "stock":

            # Extract symbol using AI
            with st.spinner("🔍 Extracting stock symbol..."):
                symbol_prompt = f"""
                Extract the stock ticker symbol from this query.
                Query: {user_input}
                Reply with ONLY the ticker symbol like: AAPL, TSLA, RELIANCE.NS
                For Indian stocks add .NS at end like: TCS.NS, INFY.NS
                Nothing else. Just the symbol.
                """
                symbol_response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": symbol_prompt}]
                )
                symbol = symbol_response.choices[0].message.content.strip()

            st.info(f"📊 Fetching data for: **{symbol}**")

            # Get live metrics
            with st.spinner("📈 Fetching live data..."):
                metrics = get_stock_metrics(symbol)

            if metrics:
                # Show key metrics
                st.subheader(f"📊 {metrics.get('name', symbol)}")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "💰 Price",
                        f"${metrics['current_price']}",
                        f"{metrics['change']} ({metrics['change_pct']}%)"
                    )
                with col2:
                    st.metric(
                        "📈 52W High",
                        f"${metrics['52w_high']}"
                    )
                with col3:
                    st.metric(
                        "📉 52W Low",
                        f"${metrics['52w_low']}"
                    )
                with col4:
                    st.metric(
                        "📊 P/E Ratio",
                        metrics['pe_ratio']
                    )

                st.divider()

                # Show chart
                with st.spinner("📊 Generating chart..."):
                    chart = get_stock_chart(symbol)

                if chart:
                    st.plotly_chart(
                        chart,
                        use_container_width=True
                    )
                else:
                    st.warning("Chart not available")

                st.divider()

            # News Sentiment
            with st.spinner("📰 Fetching live news..."):
                company_name = metrics.get('name', symbol)
                news_data = None
                try:
                    from pipelines.stock_pipeline import get_news_sentiment
                    news_data = get_news_sentiment(company_name, symbol)
                except Exception as _e:
                    news_data = {}

            if news_data:
                st.subheader("📰 News Sentiment Analysis")

                # Parse sentiment
                sentiment_text = news_data.get("sentiment", "")
                
                # Extract values
                positive = 0
                negative = 0
                neutral = 0
                overall = "NEUTRAL"
                summary = ""

                for line in sentiment_text.split("\n"):
                    if "POSITIVE:" in line:
                        try:
                            positive = int(line.split(":")[1].strip().replace("%",""))
                        except:
                            positive = 0
                    elif "NEGATIVE:" in line:
                        try:
                            negative = int(line.split(":")[1].strip().replace("%",""))
                        except:
                            negative = 0
                    elif "NEUTRAL:" in line:
                        try:
                            neutral = int(line.split(":")[1].strip().replace("%",""))
                        except:
                            neutral = 0
                    elif "OVERALL:" in line:
                        overall = line.split(":")[1].strip()
                    elif "SUMMARY:" in line:
                        summary = line.split(":")[1].strip()

                # Sentiment metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🟢 Positive", f"{positive}%")
                with col2:
                    st.metric("🔴 Negative", f"{negative}%")
                with col3:
                    st.metric("⚪ Neutral", f"{neutral}%")
                with col4:
                    overall_emoji = "🟢" if "BULL" in overall else "🔴" if "BEAR" in overall else "⚪"
                    st.metric("📊 Overall", f"{overall_emoji} {overall}")

                # Summary
                if summary:
                    st.info(f"**AI Summary:** {summary}")

                # Headlines
                st.markdown("**📋 Recent Headlines:**")
                for headline in news_data.get("headlines", [])[:5]:
                    st.markdown(f"""
                    <div style="
                        background: #1a1a2e;
                        padding: 10px 15px;
                        border-radius: 8px;
                        margin: 5px 0;
                        border-left: 3px solid #FF6B35;
                    ">
                    📰 <a href="{headline['url']}" 
                          target="_blank" 
                          style="color: #e0e0e0; 
                                 text-decoration: none;">
                        {headline['title']}
                    </a>
                    <br>
                    <small style="color: #888;">
                        📅 {headline['published']}
                    </small>
                    </div>
                    """, unsafe_allow_html=True)

                st.divider()

            # AI Analysis
            with st.spinner("🤖 AI analyzing..."):
                output = run_stock_pipeline(user_input)
            st.subheader("🤖 AI Analysis")
            analysis_placeholder = st.empty()
            stream_text_response(output, analysis_placeholder)
            # persist as structured stock message so chart/metrics can be re-rendered
            assistant_message = {
                "role": "assistant",
                "content": output,
                "type": "stock",
                "symbol": symbol,
                "metrics": metrics
            }

        elif domain == "code":
            with st.spinner("💻 Code pipeline running..."):
                output = run_code_pipeline(user_input)
            st.subheader("💻 Code Review")
            code_placeholder = st.empty()
            stream_text_response(output, code_placeholder)

        elif domain == "job":
            with st.spinner("💼 Job pipeline running..."):
                output = run_job_pipeline(user_input)
            st.subheader("💼 Job Application Report")
            job_placeholder = st.empty()
            stream_text_response(output, job_placeholder)

        else:
            output = "Sorry, I could not process your query!"
            st.markdown(output)

        # Pin button for the latest response
        if output:
            if st.button(
                "📌 Pin this response",
                key=f"pin_last_{len(st.session_state.messages)}",
                help="Pin this AI response together with the user prompt"
            ):
                title = user_input[:40] + "..."
                already_pinned = any(
                    p.get('content') == output
                    for p in get_all_pins()
                )
                if not already_pinned:
                    add_pin(user_input, output, title=title)
                    st.session_state.pinned = get_all_pins()
                    st.success("📌 Pinned!")
                else:
                    st.warning("Already pinned!")

        # Save to history
        if domain in ("image", "stock"):
            st.session_state.messages.append(assistant_message)
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": output
            })
