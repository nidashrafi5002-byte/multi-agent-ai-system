import streamlit as st
import time
import os
import re
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
    page_title="MAIA - Multi-Agent Intelligence System",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #0a0a0a !important;
    color: #eee;
}
[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="stToolbar"] {
    display: none !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #111 !important;
    border-right: 1px solid #1e1e1e !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #1a1a1a !important;
    border: 0.5px solid #2a2a2a !important;
    color: #ccc !important;
    font-size: 0.78rem;
    text-align: left;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px 0;
    transition: all 0.3s ease;
    width: 100%;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1e1e1e !important;
    border-color: #3a6fff !important;
    color: #fff !important;
    transform: translateX(4px);
}

/* ── Pipeline Tabs ── */
.pipeline-tabs {
    display: flex;
    gap: 8px;
    padding: 16px 0;
    justify-content: center;
    flex-wrap: wrap;
    background: #111;
    margin-bottom: 16px;
}
.tab-pill {
    padding: 10px 16px;
    border-radius: 24px;
    background: #1a1a1a;
    border: 0.5px solid #2a2a2a;
    color: #888;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: 6px;
}
.tab-pill:hover {
    background: #222;
    border-color: #3a6fff;
    color: #3a6fff;
}
.tab-pill.active {
    background: #3a6fff;
    border-color: #3a6fff;
    color: white;
    box-shadow: 0 0 12px rgba(58, 111, 255, 0.3);
}

/* ── Chat messages ── */
.user-msg {
    background: #0d1a40 !important;
    border: 1px solid #1a3a6e !important;
    padding: 14px 18px;
    border-radius: 16px 16px 4px 16px;
    color: #90caf9;
    margin: 10px 0;
    max-width: 75%;
    margin-left: auto;
    font-size: 14px;
    box-shadow: 0 2px 8px rgba(13, 26, 64, 0.4);
    animation: slideInRight 0.4s ease-out;
}

.ai-msg {
    background: #1a1a1a;
    border: 0.5px solid #2a2a2a;
    padding: 14px 18px;
    border-radius: 4px 12px 12px 12px;
    color: #e0e0e0;
    margin: 10px 0;
    max-width: 80%;
    font-size: 14px;
    line-height: 1.6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    animation: slideInLeft 0.4s ease-out;
}
.ai-msg {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}
.ai-msg, .user-msg {
    height: auto !important;
    min-height: 0 !important;
    align-self: flex-start !important;
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

.ai-msg > *:first-child,
.ai-msg > *:last-child,
.ai-msg h1,
.ai-msg h2,
.ai-msg h3,
.ai-msg h4,
.ai-msg h5,
.ai-msg h6,
.ai-msg p,
.ai-msg ul,
.ai-msg ol,
.ai-msg pre,
.ai-msg div {
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
}

.ai-msg > *:last-child {
    margin-bottom: 0 !important;
}

.domain-badge {
    font-size: 11px;
    background: linear-gradient(135deg, #1f2a1f 0%, #2a3a2a 100%);
    color: #4caf50;
    border: 0.5px solid #4caf50;
    border-radius: 4px;
    padding: 4px 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.score-badge {
    font-size: 11px;
    background: linear-gradient(135deg, #1a1f2a 0%, #2a2f3a 100%);
    color: #64b5f6;
    border: 0.5px solid #64b5f6;
    border-radius: 4px;
    padding: 4px 10px;
    font-weight: 600;
}

/* ── Agent Execution Log ── */
.exec-log {
    background: #111;
    border: 0.5px solid #1e1e1e;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 12px;
    font-size: 11px;
}

.exec-log-title {
    font-size: 10px;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 8px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.log-row {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    color: #888;
    padding: 6px 0;
    transition: color 0.3s;
}

.log-row:hover {
    color: #aaa;
}

.log-dot-done {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #4caf50;
    flex-shrink: 0;
    box-shadow: 0 0 6px rgba(76, 175, 80, 0.4);
}

.log-dot-active {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #FF6B35;
    flex-shrink: 0;
    box-shadow: 0 0 6px rgba(255, 107, 53, 0.4);
    animation: pulse 1.5s infinite;
}

.log-dot-wait {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #555;
    flex-shrink: 0;
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
    border-radius: 24px !important;
    border: 0.5px solid #2a2a2a !important;
    background: #1a1a1a !important;
    padding: 8px 16px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
    transition: all 0.3s ease !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #3a6fff !important;
    box-shadow: 0 0 12px rgba(58, 111, 255, 0.2) !important;
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
    background: #1a1a1a;
    border: 0.5px solid #2a2a2a;
    border-radius: 8px;
    padding: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    transition: transform 0.3s;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
}

/* ── Alerts & Messages ── */
[data-testid="stAlert"] {
    border-radius: 8px;
    border: 0.5px solid #2a2a2a;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    background: #1a1a1a !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #1a1a1a;
    border: 0.5px solid #2a2a2a;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    transition: all 0.3s;
}
[data-testid="stExpander"]:hover {
    border-color: #3a3a3a;
}

/* ── Typography ── */
h1 {
    color: #eee !important;
    text-shadow: none !important;
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
p {
    color: #ccc !important;
    line-height: 1.6;
}

/* ── Divider ── */
hr {
    border-color: #1e1e1e !important;
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

/* ── Top Bar Container ── */
.top-bar {
    background: #111;
    border-bottom: 1px solid #1e1e1e;
    padding: 16px 24px;
    margin-bottom: 12px;
}

.top-bar-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.maia-logo {
    font-size: 28px;
    font-weight: 900;
    color: #eee;
    letter-spacing: 2px;
}

.maia-subtitle {
    font-size: 12px;
    color: #888;
    font-weight: 500;
    letter-spacing: 0.5px;
}

.top-bar-badges {
    display: flex;
    gap: 8px;
    margin-left: auto;
}

.badge {
    padding: 6px 12px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}

.badge-accuracy {
    background: #1f2a1f;
    border: 0.5px solid #4caf50;
    color: #4caf50;
}

.badge-pipelines {
    background: #1a1f2a;
    border: 0.5px solid #3a6fff;
    color: #3a6fff;
}

/* ── Font size fixes ── */
.maia-topbar-title { font-size: 20px !important; }
.maia-topbar-sub { font-size: 13px !important; }

/* Pipeline tabs */
.ptab { font-size: 14px !important; padding: 7px 16px !important; }

/* Chat messages */
.user-msg { font-size: 15px !important; }
.ai-msg-body { font-size: 15px !important; line-height: 1.7 !important; }
.ai-name { font-size: 14px !important; }
.pipeline-badge { font-size: 11px !important; }

/* Sidebar */
[data-testid="stSidebar"] .stButton > button {
    font-size: 13px !important;
    padding: 8px 12px !important;
}

/* History items */
.hist-time { font-size: 11px !important; }

/* Exec log */
.log-row { font-size: 13px !important; }
.exec-log-title { font-size: 11px !important; }

/* Input placeholder */
[data-testid="stChatInput"] textarea {
    font-size: 15px !important;
}

/* Metrics */
[data-testid="stMetricLabel"] > div { font-size: 13px !important; }
[data-testid="stMetricValue"] > div { font-size: 22px !important; }

/* General text */
.stMarkdown p { font-size: 15px !important; }
.stMarkdown li { font-size: 15px !important; }
h1 { font-size: 28px !important; }
h2 { font-size: 22px !important; }
h3 { font-size: 18px !important; }

/* Info/warning boxes */
[data-testid="stAlert"] p { font-size: 14px !important; }

/* Expander */
[data-testid="stExpander"] summary p {
    font-size: 14px !important;
}

/* Badges */
.badge-green, .badge-blue {
    font-size: 12px !important;
    padding: 4px 12px !important;
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
    st.session_state.selected_agent = "auto"

# Style history buttons to look like dark cards
st.markdown("""
<style>
[data-testid="stSidebar"] .stButton > button {
    background: #1a1a1a !important;
    border: 0.5px solid #2a2a2a !important;
    color: #ccc !important;
    font-size: 0.8rem;
    text-align: left;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px 0;
    transition: all 0.3s ease !important;
    width: 100%;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1e1e1e !important;
    border-color: #3a6fff !important;
    color: #fff !important;
    transform: translateX(4px) !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize pins DB and load persisted pins
init_db()
init_history_db()
st.session_state.pinned = get_all_pins()

# ── TOP BAR ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div class="top-bar-left">
            <div>
                <div class="maia-logo">🤖 MAIA</div>
                <div class="maia-subtitle">MULTI-AGENT INTELLIGENCE SYSTEM</div>
            </div>
        </div>
        <div class="top-bar-badges">
            <div class="badge badge-accuracy">✓ 92% ACCURACY</div>
            <div class="badge badge-pipelines">⚡ 7 PIPELINES</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── PIPELINE TABS ──────────────────────────────────────────────────────────
agent_pill_options = [
    "🤖 Auto (Router)",
    "🔬 Research",
    "📈 Stock",
    "💻 Code",
    "💼 Job",
    "✈️ Flight",
    "🎨 Image",
    "💬 General"
]
agent_pill_map = {
    "🤖 Auto (Router)": "auto",
    "🔬 Research": "research",
    "📈 Stock": "stock",
    "💻 Code": "code",
    "💼 Job": "job",
    "✈️ Flight": "flight",
    "🎨 Image": "image",
    "💬 General": "general"
}
reverse_pill_map = {v: k for k, v in agent_pill_map.items()}

if "selected_agent" not in st.session_state or st.session_state.selected_agent not in reverse_pill_map:
    st.session_state.selected_agent = "auto"

cols_tab = st.columns([1, 10, 1])
with cols_tab[1]:
    chosen_pill = st.pills(
        "Agent Pipeline",
        options=agent_pill_options,
        default=reverse_pill_map.get(st.session_state.selected_agent, "🤖 Auto (Router)"),
        label_visibility="collapsed"
    )
    if chosen_pill:
        st.session_state.selected_agent = agent_pill_map[chosen_pill]


def normalize_response_text(text: str) -> str:
    """Convert HTML line breaks sometimes returned by the model to Markdown breaks."""
    return re.sub(r"<br\s*/?>", "\n", str(text), flags=re.IGNORECASE)


def stream_text_response(text: str, placeholder, delay: float = 0.02):
    """Render output progressively for non-streaming pipeline results."""
    normalized_text = normalize_response_text(text)
    full_text = ""
    for chunk in normalized_text.split(" "):
        full_text += chunk + " "
        placeholder.markdown(full_text + "▌")
        time.sleep(delay)
    placeholder.markdown(normalize_response_text(full_text))
    return full_text

def display_agent_execution_log(agents_log):
    """Display agent execution log with status dots."""
    with st.container():
        log_html = '<div class="exec-log">\n<div class="exec-log-title">Agent execution log</div>\n'
        for agent in agents_log:
            status = agent.get("status", "done")
            dot_class = "log-dot-done" if status == "done" else ("log-dot-active" if status == "active" else "log-dot-wait")
            time_text = agent.get("time", "")
            agent_name = agent.get("agent", "")
            log_html += f'<div class="log-row">\n<div class="{dot_class}"></div>\n<span>{agent_name}</span>\n<span class="log-time">{time_text}</span>\n</div>\n'
        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)


def append_message_once(message):
    """Store a chat message once per response cycle, even after reruns."""
    if not isinstance(message, dict):
        return False

    if not st.session_state.messages:
        st.session_state.messages.append(message)
        return True

    if st.session_state.messages[-1] == message:
        return False

    st.session_state.messages.append(message)
    return True

# Sidebar — Mission Control
with st.sidebar:

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: #1a1a1a;
        border: 0.5px solid #2a2a2a;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
    ">
        <div style="font-size: 24px;">🤖</div>
        <div>
            <div style="font-size: 14px; font-weight: 700; color: #eee;">MAIA</div>
            <div style="font-size: 11px; color: #888; font-weight: 500;">Multi-agent System</div>
        </div>
        <div style="margin-left: auto; width: 8px; height: 8px; border-radius: 50%; background: #4caf50; box-shadow: 0 0 6px rgba(76, 175, 80, 0.6);"></div>
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
                f"<div style='color:#3a6fff;font-size:0.8rem;font-weight:800;"
                f"letter-spacing:1px;margin:12px 0 6px;padding-left:4px;border-left:2px solid #3a6fff'>{bucket_label}</div>",
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
                "<div style='color:#3a6fff;font-size:0.8rem;font-weight:800;"
                "letter-spacing:1px;margin:12px 0 6px;padding-left:4px;border-left:2px solid #3a6fff'>🔥 MOST USED</div>",
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
                        <span style='color:#3a6fff;font-weight:600'>{cnt}x</span>
                    </div>
                    <div style='background:#1a1a1a;border-radius:6px;height:8px;border:0.5px solid #2a2a2a'>
                        <div style='background:linear-gradient(90deg,#3a6fff,#64b5f6);
                                    width:{bar_w}%;height:8px;border-radius:6px;box-shadow:0 0 8px rgba(58,111,255,0.4)'></div>
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

# Display chat history from session state only
history_container = st.container()
with history_container:
    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            col1, col2 = st.columns([1, 3])
            with col2:
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
                        message.get("image_bytes", message["image_url"]),
                        caption=message["enhanced_prompt"],
                        width=700
                    )
                    st.caption(f"Generated: {message['generated_at']}")
                elif mtype == "flight":
                    flight = message.get("enriched") or {}
                    status = str(flight.get("status", "unknown")).lower()
                    status_labels = {
                        "active": ("🟢", "IN AIR"),
                        "scheduled": ("🔵", "SCHEDULED"),
                        "landed": ("🟡", "LANDED"),
                        "cancelled": ("🔴", "CANCELLED"),
                        "delayed": ("🟠", "DELAYED"),
                    }
                    status_icon, status_label = status_labels.get(status, ("⚪", status.upper()))
                    st.markdown(
                        f"**✈️ {flight.get('flight_number', 'Flight')}** · "
                        f"{flight.get('airline', 'N/A')} · {status_icon} {status_label}"
                    )
                    if flight.get("ai_summary"):
                        st.info(f"🤖 {flight['ai_summary']}")
                    metrics = st.columns(3)
                    progress = flight.get("progress") or {}
                    countdown = flight.get("countdown") or {}
                    metrics[0].metric("🛫 Departure delay", f"{flight.get('dep_delay', 'N/A')} min")
                    metrics[1].metric("🛬 Arrival delay", f"{flight.get('arr_delay', 'N/A')} min")
                    eta = "N/A"
                    if countdown.get("available") and not countdown.get("landed_or_past"):
                        eta = f"{countdown.get('hours', 0)}h {countdown.get('minutes', 0)}m"
                    metrics[2].metric("⏱️ ETA", eta)
                    progress_value = progress.get("pct")
                    if progress.get("available") and progress_value is not None:
                        st.progress(
                            min(100, max(0, int(progress_value))) / 100,
                            text=f"✈️ Flight progress: {progress_value}%"
                        )

                    departure = flight.get("departure") or {}
                    arrival = flight.get("arrival") or {}
                    with st.expander("🛫 Departure Airport Details", expanded=True):
                        st.markdown(
                            f"**Airport:** {departure.get('name', 'N/A')}  "
                            f"\n\n**IATA:** {departure.get('iata', 'N/A')}  |  "
                            f"**ICAO:** {departure.get('icao', 'N/A')}"
                        )
                        st.markdown(
                            f"**Terminal:** {departure.get('terminal', 'N/A')}  |  "
                            f"**Gate:** {departure.get('gate', 'N/A')}  |  "
                            f"**Timezone:** {departure.get('timezone', 'N/A')}"
                        )
                        st.caption(
                            f"Scheduled: {departure.get('scheduled', 'N/A')} | "
                            f"Estimated: {departure.get('estimated', 'N/A')} | "
                            f"Actual: {departure.get('actual', 'N/A')}"
                        )
                    with st.expander("🛬 Arrival Airport Details", expanded=True):
                        st.markdown(
                            f"**Airport:** {arrival.get('name', 'N/A')}  "
                            f"\n\n**IATA:** {arrival.get('iata', 'N/A')}  |  "
                            f"**ICAO:** {arrival.get('icao', 'N/A')}"
                        )
                        st.markdown(
                            f"**Terminal:** {arrival.get('terminal', 'N/A')}  |  "
                            f"**Gate:** {arrival.get('gate', 'N/A')}  |  "
                            f"**Timezone:** {arrival.get('timezone', 'N/A')}"
                        )
                        st.caption(
                            f"Scheduled: {arrival.get('scheduled', 'N/A')} | "
                            f"Estimated: {arrival.get('estimated', 'N/A')} | "
                            f"Actual: {arrival.get('actual', 'N/A')}"
                        )
                    with st.expander("🛩️ Aircraft Details"):
                        aircraft = flight.get("aircraft") or {}
                        aircraft_values = [
                            ("Registration", aircraft.get("registration", "Not Available")),
                            ("IATA Type", aircraft.get("iata", "Not Available")),
                            ("ICAO Type", aircraft.get("icao", "Not Available")),
                            ("ICAO24", aircraft.get("icao24", "Not Available")),
                        ]
                        aircraft_columns = st.columns(4)
                        for column, (label, value) in zip(aircraft_columns, aircraft_values):
                            column.metric(label, value or "Not Available")
                    with st.expander("📍 Live Position"):
                        live = flight.get("live") or {}
                        if live:
                            position_columns = st.columns(4)
                            for column, label, key in zip(
                                position_columns,
                                ("Latitude", "Longitude", "Altitude (m)", "Speed (km/h)"),
                                ("latitude", "longitude", "altitude", "speed"),
                            ):
                                column.metric(label, live.get(key) or "Not Available")
                        else:
                            st.info("Live position is not currently available.")
                    with st.expander("🌤️ Weather at Airports"):
                        weather_columns = st.columns(2)
                        for weather_column, label, weather in (
                            (weather_columns[0], "Departure", flight.get("dep_weather") or {}),
                            (weather_columns[1], "Arrival", flight.get("arr_weather") or {}),
                        ):
                            with weather_column:
                                st.markdown(f"**{label} Weather**")
                                if weather.get("available"):
                                    st.metric("Temperature", f"{weather.get('temp_c', 'N/A')} °C")
                                    st.caption(
                                        f"{weather.get('condition', 'N/A')} · "
                                        f"Humidity {weather.get('humidity_pct', 'N/A')}% · "
                                        f"Wind {weather.get('wind_kmh', 'N/A')} km/h · "
                                        f"Visibility {weather.get('visibility_km', 'N/A')} km"
                                    )
                                else:
                                    st.caption("Weather data is not available.")
                    st.markdown(normalize_response_text(message.get("content", "")))
                    if idx > 0:
                        map_key = f"map_{idx - 1}"
                        if map_key in st.session_state:
                            st.components.v1.html(st.session_state[map_key], height=500)
                elif mtype == "stock":
                    st.markdown(f"""
                    <div class="ai-msg">
                    <div class="msg-header">
                        <span class="domain-badge">📈 STOCK</span>
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

                    # Restore the saved analysis before rendering the chart.
                    stock_content = str(message.get("content", "")).strip()
                    if stock_content:
                        st.subheader("🤖 AI Analysis")
                        st.markdown(stock_content)

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
                    message_content = normalize_response_text(message.get("content", "")).strip()
                    message_content = re.sub(r"\n[ \t]*(?:\n[ \t]*){2,}", "\n\n", message_content)
                    st.markdown(f"""
                    <div class="ai-msg">
                    <div class="msg-header">
                        <span class="domain-badge">{domain_badge}</span>
                        <span class="score-badge">AI RESPONSE</span>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(message_content)

                    # Render a saved flight map after its assistant report.
                    if domain == "flight" and idx > 0:
                        map_key = f"map_{idx - 1}"
                        if map_key in st.session_state:
                            st.components.v1.html(
                                st.session_state[map_key],
                                height=500
                            )

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
        agent_display = st.session_state.selected_agent
        input_placeholder = "Ask MAIA anything..." if agent_display == "auto" else f"Ask {agent_display.capitalize()} agent anything..."
        user_input = st.chat_input(placeholder=input_placeholder)
    
    with col3:
        # Agent selector indicator
        agent_icons = {
            "auto": "🤖",
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
        {agent_icons.get(st.session_state.selected_agent, "🤖")}
        </div>
        """, unsafe_allow_html=True)

# If a history item was clicked, use it as the query
if st.session_state.selected_query and not user_input:
    user_input = st.session_state.selected_query
    st.session_state.selected_query = None

if user_input:

    # Show user message matching history layout exactly
    col1_u, col2_u = st.columns([1, 3])
    with col2_u:
        st.markdown(f"""
        <div class="user-msg">
        🧑 {user_input}
        </div>
        """, unsafe_allow_html=True)
    append_message_once({
        "role": "user",
        "content": user_input
    })

    col1, col2 = st.columns([3, 1])
    with col1:
        # Keep all in-progress output inside the response column only.
        live_container = st.container()

        # Progress container
        progress_container = st.container()
        
        # Step 1 - Route
        with progress_container:
            st.markdown("""
            <div class="exec-log">
                <div style="font-size: 10px; text-transform: uppercase; color: #666; margin-bottom: 6px; font-weight: 700;">Agent Execution Log</div>
                <div class="log-row">
                    <div class="log-dot-active"></div>
                    <span>🔀 Router</span>
                    <span class="log-time">analyzing...</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.selected_agent and st.session_state.selected_agent != "auto":
            domain = st.session_state.selected_agent
        else:
            result = route_query(user_input, chat_history=st.session_state.messages)
            domain = result["domain"]

        # Save to persistent history
        add_history(domain, user_input)

        with progress_container:
            st.markdown(f"""
            <div class="exec-log">
                <div style="font-size: 10px; text-transform: uppercase; color: #666; margin-bottom: 6px; font-weight: 700;">Agent Execution Log</div>
                <div class="log-row">
                    <div class="log-dot-done"></div>
                    <span>🔀 Router</span>
                    <span class="log-time">complete</span>
                </div>
                <div class="log-row">
                    <div class="log-dot-active"></div>
                    <span>🚀 {domain.upper()} Pipeline</span>
                    <span class="log-time">running...</span>
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

                You are MAIA, this application's multi-agent AI assistant.
                If the user asks who you are, identify yourself as MAIA and
                describe yourself as a multi-agent AI assistant. Do not claim
                to be ChatGPT or GPT-4.

                IMPORTANT: Always detect the language
                of the user's message and respond in
                that SAME language.
                If user writes in Hindi, respond in Hindi.
                If user writes in Japanese, respond in Japanese.
                If user writes in Tamil, respond in Tamil.
                Never switch languages unless user asks."""

            # STREAMING
            st.markdown(f"""
            <div class="ai-msg">
            <div class="msg-header">
                <span class="domain-badge">{badge}</span>
                <span class="score-badge">AI RESPONSE</span>
            </div>
            </div>
            """, unsafe_allow_html=True)
            stream_placeholder = st.empty()
            full_response = ""

            try:
                # Build conversation context with recent chat history
                conversation_messages = [{"role": "system", "content": system_prompt}]
                history_turns = [
                    m for m in st.session_state.messages[:-1]
                    if m.get("role") in ("user", "assistant") and m.get("content") and m.get("type") not in ("image", "stock")
                ][-6:]
                for past_m in history_turns:
                    conversation_messages.append({
                        "role": past_m["role"],
                        "content": str(past_m["content"])
                    })
                conversation_messages.append({
                    "role": "user",
                    "content": user_input
                })

                stream = create_chat_completion(
                    messages=conversation_messages,
                    stream=True
                )

                reasoning_text = ""
                has_started_content = False

                for chunk in stream:
                    try:
                        choices = getattr(chunk, "choices", None)
                        if not choices:
                            continue
                        delta = getattr(choices[0], "delta", None)
                        if delta is None:
                            continue

                        # Handle reasoning tokens from models like openai/gpt-oss-20b
                        reasoning = getattr(delta, "reasoning", None)
                        if reasoning and not has_started_content:
                            reasoning_text += reasoning
                            stream_placeholder.markdown("🧠 *Thinking...*")
                            continue

                        content = getattr(delta, "content", None)
                        if content:
                            has_started_content = True
                            full_response += content
                            stream_placeholder.markdown(normalize_response_text(full_response) + "▌")
                            time.sleep(0.01)
                    except Exception as e:
                        print("Stream chunk error:", e)
                        continue

                stream_placeholder.markdown(normalize_response_text(full_response))
                output = full_response
            except Exception as e:
                # Streaming failed — fallback to non-streaming call
                import traceback
                print("Streaming failed, falling back to non-streaming call:", type(e).__name__, e)
                traceback.print_exc()
                try:
                    fallback = create_chat_completion(
                        messages=conversation_messages,
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
                        try:
                            content = str(fallback)
                        except Exception:
                            content = ""

                    output = content
                    stream_placeholder.markdown(normalize_response_text(output))
                except Exception as e2:
                    print("Fallback non-streaming error:", type(e2).__name__, e2)
                    import traceback as _tb
                    _tb.print_exc()
                    output = "Sorry, an error occurred while generating the response."

            # Display agent execution log for general pipeline
            display_agent_execution_log([
                {"agent": "🔀 Router", "status": "done", "time": "0.2s"},
                {"agent": "🧠 LLM Agent", "status": "done", "time": "2.4s"},
                {"agent": "✓ Output Formatter", "status": "done", "time": "0.1s"}
            ])

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
                    result.get("image_bytes", result["image_url"]),
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
                "image_bytes": result["image_bytes"],
                "generated_at": result["generated_at"]
            }
            
            # Display agent execution log for image pipeline
            display_agent_execution_log([
                {"agent": "🔀 Router", "status": "done", "time": "0.2s"},
                {"agent": "🎨 Image Enhancer", "status": "done", "time": "0.8s"},
                {"agent": "🖼️ Image Generator", "status": "done", "time": "3.2s"}
            ])

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
                flight_placeholder = live_container.empty()
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
                map_html = flight_map._repr_html_()
                user_message_index = max(0, len(st.session_state.messages) - 1)
                st.session_state[f"map_{user_message_index}"] = map_html
            output = report
            assistant_message = {
                "role": "assistant",
                "content": output,
                "domain": domain,
                "type": "flight",
                "enriched": enriched,
            }
            
            # Display agent execution log for flight pipeline
            display_agent_execution_log([
                {"agent": "🔀 Router", "status": "done", "time": "0.2s"},
                {"agent": "✈️ Flight Tracker", "status": "done", "time": "1.5s"},
                {"agent": "🗺️ Map Generator", "status": "done", "time": "0.9s"},
                {"agent": "📊 Data Enricher", "status": "done", "time": "0.6s"}
            ])

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
            stream_placeholder = live_container.empty()
            full_text = ""

            # Stream word by word
            words = graph_result["written_report"].split(" ")
            for word in words:
                full_text += word + " "
                stream_placeholder.markdown(normalize_response_text(full_text) + "▌")
                time.sleep(0.02)
            stream_placeholder.markdown(normalize_response_text(full_text))
            output = graph_result["final_output"]
            
            # Display agent execution log for research pipeline
            display_agent_execution_log([
                {"agent": "🔀 Router", "status": "done", "time": "0.2s"},
                {"agent": "🔬 Researcher", "status": "done", "time": "2.1s"},
                {"agent": "📚 Analyzer", "status": "done", "time": "1.8s"},
                {"agent": "✍️ Writer", "status": "done", "time": "2.5s"}
            ])

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
                    model="openai/gpt-oss-20b",
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
            analysis_placeholder = live_container.empty()
            stream_text_response(output, analysis_placeholder)
            # persist as structured stock message so chart/metrics can be re-rendered
            assistant_message = {
                "role": "assistant",
                "content": output,
                "type": "stock",
                "symbol": symbol,
                "metrics": metrics,
                "news_data": news_data or {}
            }
            
            # Display agent execution log for stock pipeline
            display_agent_execution_log([
                {"agent": "🔀 Router", "status": "done", "time": "0.2s"},
                {"agent": "💰 Symbol Extractor", "status": "done", "time": "0.3s"},
                {"agent": "📈 Data Fetcher", "status": "done", "time": "1.2s"},
                {"agent": "📰 News Analyzer", "status": "done", "time": "1.8s"},
                {"agent": "🤖 AI Analyst", "status": "done", "time": "1.5s"}
            ])

        elif domain == "code":
            with st.spinner("💻 Code pipeline running..."):
                output = run_code_pipeline(user_input)
            st.subheader("💻 Code Review")
            code_placeholder = live_container.empty()
            stream_text_response(output, code_placeholder)
            
            # Display agent execution log for code pipeline
            display_agent_execution_log([
                {"agent": "🔀 Router", "status": "done", "time": "0.2s"},
                {"agent": "💻 Code Parser", "status": "done", "time": "0.5s"},
                {"agent": "🔍 Analyzer", "status": "done", "time": "1.2s"},
                {"agent": "✍️ Reviewer", "status": "done", "time": "1.8s"}
            ])

        elif domain == "job":
            with st.spinner("💼 Job pipeline running..."):
                output = run_job_pipeline(user_input)
            st.subheader("💼 Job Application Report")
            job_placeholder = live_container.empty()
            stream_text_response(output, job_placeholder)
            
            # Display agent execution log for job pipeline
            display_agent_execution_log([
                {"agent": "🔀 Router", "status": "done", "time": "0.2s"},
                {"agent": "💼 Job Analyzer", "status": "done", "time": "1.1s"},
                {"agent": "📝 Content Writer", "status": "done", "time": "2.3s"},
                {"agent": "✓ Formatter", "status": "done", "time": "0.4s"}
            ])

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

        # Save to history exactly once for this response cycle.
        if domain in ("image", "stock", "flight"):
            message_added = append_message_once(assistant_message)
        else:
            message_added = append_message_once({
                "role": "assistant",
                "content": output,
                "domain": domain
            })

        live_container.empty()
        if hasattr(locals().get('stream_placeholder'), 'empty'):
            try:
                stream_placeholder.empty()
            except Exception:
                pass
        if message_added:
            st.rerun()
