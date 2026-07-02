"""
BA Intelligence Toolkit — Main Streamlit Application
A compliance gap reasoning tool for UK banking business analysts.

Run:  streamlit run app.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

from dotenv import load_dotenv
load_dotenv()

# Ensure local modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from ai_engine import AIEngine
from modules.extractor import RequirementsExtractor
from modules.compliance import ComplianceGapChecker
from modules.rtm import RTMGenerator
from modules.gap_analyzer import GapAnalyzer
from utils import (
    load_text_file,
    load_uploaded_file,
    export_to_excel,
    create_compliance_heatmap,
    create_gap_priority_matrix,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BA Intelligence Toolkit",
    page_icon="\U0001F50D",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Dark theme CSS — Bloomberg Terminal / Palantir inspired
# ---------------------------------------------------------------------------
DARK_CSS = """
<style>
/* ── Root variables ─────────────────────────────────────────────── */
:root {
    --bg-primary: #0A0E1A;
    --bg-card: #111827;
    --bg-sidebar: #0D1117;
    --accent-cyan: #00D4FF;
    --accent-blue: #3B82F6;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --text-primary: #F9FAFB;
    --text-secondary: #9CA3AF;
    --border: #1F2937;
    --font-mono: 'JetBrains Mono', 'Courier New', monospace;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── Global background ──────────────────────────────────────────── */
.stApp {
    background-color: var(--bg-primary);
    background-image:
        radial-gradient(circle at 1px 1px, rgba(255,255,255,0.025) 1px, transparent 0);
    background-size: 24px 24px;
    color: var(--text-primary);
    font-family: var(--font-sans);
}

/* ── Sidebar ────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-primary);
}

/* ── Tool name in sidebar ──────────────────────────────────────── */
.sidebar-title {
    color: var(--accent-cyan) !important;
    font-family: var(--font-sans);
    font-weight: 700;
    letter-spacing: 0.5px;
    font-size: 1.3rem;
}

/* ── Main content headers ──────────────────────────────────────── */
h1, h2, h3, h4 {
    color: var(--text-primary) !important;
    font-family: var(--font-sans);
    letter-spacing: -0.02em;
}
h1 {
    font-weight: 700;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
}
h3 {
    text-transform: uppercase;
    font-size: 0.85rem;
    letter-spacing: 0.08em;
    color: var(--text-secondary) !important;
    font-weight: 600;
}

/* ── Cards / panels ─────────────────────────────────────────────── */
.stCard {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}

/* ── Metric cards (Bloomberg-style number cards) ───────────────── */
div[data-testid="stMetric"] {
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 16px 20px;
}
div[data-testid="stMetric"] label {
    color: var(--text-secondary) !important;
    font-size: 0.7rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--accent-cyan) !important;
    font-family: var(--font-mono) !important;
    font-size: 2rem !important;
    font-weight: 700;
}

/* ── Buttons: terminal-style ───────────────────────────────────── */
.stButton > button[kind="primary"] {
    background-color: transparent !important;
    color: var(--accent-cyan) !important;
    border: 1px solid var(--accent-cyan) !important;
    border-radius: 4px !important;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.1em;
    font-size: 0.8rem;
    font-family: var(--font-sans);
    transition: all 0.2s ease;
}
.stButton > button[kind="primary"]:hover {
    background-color: rgba(0, 212, 255, 0.1) !important;
    border-color: var(--accent-cyan) !important;
}
.stButton > button[kind="secondary"] {
    background-color: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    text-transform: uppercase;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--accent-blue) !important;
    color: var(--accent-blue) !important;
}

/* ── Text inputs ────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-sans);
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 1px var(--accent-cyan) !important;
}

/* ── Selectbox / Radio ──────────────────────────────────────────── */
.stSelectbox > div > div,
.stRadio > div {
    background-color: var(--bg-card) !important;
}

/* ── Dataframes ─────────────────────────────────────────────────── */
.stDataFrame {
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
}
.stDataFrame [data-testid="stDataFrame"] {
    background-color: var(--bg-card) !important;
}

/* ── Expanders (gap cards) ──────────────────────────────────────── */
.streamlit-expanderHeader {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    font-family: var(--font-sans);
    font-size: 0.85rem;
}
.streamlit-expanderContent {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 4px 4px !important;
}

/* ── Severity border classes for gap cards ──────────────────────── */
.severity-high {
    border-left: 3px solid var(--danger) !important;
}
.severity-medium {
    border-left: 3px solid var(--warning) !important;
}
.severity-low {
    border-left: 3px solid var(--success) !important;
}

/* ── Alerts ─────────────────────────────────────────────────────── */
.stAlert {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
}

/* ── Info box ───────────────────────────────────────────────────── */
.stAlert [data-testid="stAlertContent"] {
    color: var(--text-primary) !important;
}

/* ── Checkboxes ─────────────────────────────────────────────────── */
.stCheckbox label {
    color: var(--text-secondary) !important;
}

/* ── File uploader ──────────────────────────────────────────────── */
.stFileUploader {
    border: 1px dashed var(--border) !important;
    border-radius: 4px;
}

/* ── Spinner ────────────────────────────────────────────────────── */
.stSpinner > div {
    color: var(--accent-cyan) !important;
}

/* ── Monospace utility ──────────────────────────────────────────── */
.mono {
    font-family: var(--font-mono) !important;
}
.mono-num {
    font-family: var(--font-mono) !important;
    color: var(--accent-cyan) !important;
    font-weight: 700;
}

/* ── Panel title (dashboard-style) ─────────────────────────────── */
.panel-title {
    font-family: var(--font-sans);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-secondary);
    font-weight: 600;
    margin-bottom: 0.5rem;
}

/* ── Divider ────────────────────────────────────────────────────── */
hr, .stMarkdown hr {
    border-color: var(--border) !important;
}

/* ── Radio (view selector) horizontal tabs ─────────────────────── */
.stRadio > div[role="radiogroup"] {
    flex-direction: row;
    gap: 0;
}
.stRadio > div[role="radiogroup"] > label {
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-right: none;
    padding: 8px 16px;
    margin: 0;
    border-radius: 0;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-secondary);
    transition: all 0.15s ease;
}
.stRadio > div[role="radiogroup"] > label:last-child {
    border-right: 1px solid var(--border);
    border-radius: 0 4px 4px 0;
}
.stRadio > div[role="radiogroup"] > label:first-child {
    border-radius: 4px 0 0 4px;
}
.stRadio > div[role="radiogroup"] > label:hover {
    color: var(--accent-cyan);
    border-color: var(--accent-cyan);
}
.stRadio > div[role="radiogroup"] > label[data-checked="true"] {
    color: var(--accent-cyan);
    border-color: var(--accent-cyan);
    background-color: rgba(0, 212, 255, 0.05);
}

/* ── Tab-style nav labels ──────────────────────────────────────── */
.nav-tabs {
    display: flex;
    gap: 2px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.nav-tab {
    padding: 8px 20px;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-secondary);
    border-bottom: 2px solid transparent;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.nav-tab.active {
    color: var(--accent-cyan);
    border-bottom-color: var(--accent-cyan);
}
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Plotly dark theme helper
# ---------------------------------------------------------------------------
def _dark_plotly_layout(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply dark theme to a Plotly figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(color="#F9FAFB", size=14)),
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#9CA3AF", family="Inter, sans-serif", size=12),
        xaxis=dict(gridcolor="#1F2937", zerolinecolor="#1F2937"),
        yaxis=dict(gridcolor="#1F2937", zerolinecolor="#1F2937"),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


# ---------------------------------------------------------------------------
# Data directory
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
CHECKLIST_PATH = DATA_DIR / "compliance_obligations.yaml"
DEMO_RESULTS_PATH = DATA_DIR / "demo_results.json"
COMPLIANCE_HISTORY_PATH = DATA_DIR / "compliance_history.json"

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "engine" not in st.session_state:
    st.session_state.engine = None
if "extractor" not in st.session_state:
    st.session_state.extractor = None
if "checker" not in st.session_state:
    st.session_state.checker = None
if "rtm_gen" not in st.session_state:
    st.session_state.rtm_gen = None
if "gap_analyzer" not in st.session_state:
    st.session_state.gap_analyzer = None
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "extraction_result" not in st.session_state:
    st.session_state.extraction_result = None
if "compliance_report" not in st.session_state:
    st.session_state.compliance_report = None
if "rtm_result" not in st.session_state:
    st.session_state.rtm_result = None
if "gap_result" not in st.session_state:
    st.session_state.gap_result = None
if "as_is_text" not in st.session_state:
    st.session_state.as_is_text = ""
if "to_be_text" not in st.session_state:
    st.session_state.to_be_text = ""
if "demo_usage" not in st.session_state:
    st.session_state.demo_usage = None
if "brd_version_label" not in st.session_state:
    st.session_state.brd_version_label = ""


# ---------------------------------------------------------------------------
# Helper: load demo results
# ---------------------------------------------------------------------------
def _load_demo_results():
    """Load pre-computed demo results from JSON file."""
    if DEMO_RESULTS_PATH.exists():
        with open(DEMO_RESULTS_PATH, "r") as f:
            data = json.load(f)
        st.session_state.input_text = data.get("input_text", "")
        st.session_state.extraction_result = data.get("extraction_result")
        st.session_state.compliance_report = data.get("compliance_report")
        st.session_state.rtm_result = data.get("rtm_result")
        st.session_state.gap_result = data.get("gap_result")
        st.session_state.as_is_text = data.get("as_is_text", "")
        st.session_state.to_be_text = data.get("to_be_text", "")
        st.session_state.demo_usage = data.get("usage")
        st.sidebar.success("Demo data loaded! Navigate to any view to see results.")
    else:
        st.sidebar.warning(
            "No demo results file found. Run the tool once with API to "
            "generate demo_results.json."
        )


# ---------------------------------------------------------------------------
# Helper: save current results as demo snapshot
# ---------------------------------------------------------------------------
def _save_demo_results():
    """Write the current session state to the demo results JSON file."""
    usage = None
    engine = st.session_state.get("engine")
    if engine:
        usage = {
            "model": engine.model,
            **engine.get_usage(),
            "cost_cny": engine.get_cost_estimate("CNY"),
        }

    snapshot = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "input_text": st.session_state.input_text,
        "extraction_result": st.session_state.extraction_result,
        "compliance_report": st.session_state.compliance_report,
        "rtm_result": st.session_state.rtm_result,
        "gap_result": st.session_state.gap_result,
        "as_is_text": st.session_state.as_is_text,
        "to_be_text": st.session_state.to_be_text,
        "usage": usage,
    }

    with open(DEMO_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    st.session_state.demo_usage = usage
    return str(DEMO_RESULTS_PATH)


# ---------------------------------------------------------------------------
# Helper: render usage / cost metrics
# ---------------------------------------------------------------------------
def _render_usage():
    """Display accumulated API usage and cost in the sidebar."""
    engine = st.session_state.get("engine")
    usage = None
    if engine:
        usage = {
            "model": engine.model,
            **engine.get_usage(),
            "cost_cny": engine.get_cost_estimate("CNY"),
        }
    elif st.session_state.get("demo_usage"):
        usage = st.session_state.demo_usage

    if usage is None:
        return

    st.sidebar.markdown("---")
    st.sidebar.markdown('<p class="panel-title">Usage & Cost</p>', unsafe_allow_html=True)
    st.sidebar.markdown(
        f'<span style="color:#9CA3AF;font-size:0.8rem;">Model:</span> '
        f'<span class="mono" style="color:#F9FAFB;">{usage.get("model", "N/A")}</span>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        f'<span style="color:#9CA3AF;font-size:0.8rem;">Calls:</span> '
        f'<span class="mono" style="color:#00D4FF;font-weight:700;">{usage.get("calls", 0)}</span>  '
        f'<span style="color:#9CA3AF;font-size:0.8rem;">Tokens:</span> '
        f'<span class="mono" style="color:#00D4FF;font-weight:700;">{usage.get("total_tokens", 0):,}</span>',
        unsafe_allow_html=True,
    )
    cost = usage.get("cost_cny", {})
    if cost and cost.get("total_cost") is not None:
        st.sidebar.markdown(
            f'<span style="color:#9CA3AF;font-size:0.8rem;">Est. cost:</span> '
            f'<span class="mono" style="color:#10B981;font-weight:700;">\u00a5{cost["total_cost"]:.4f} CNY</span>',
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            '<span style="color:#9CA3AF;font-size:0.8rem;">Est. cost: pricing not available</span>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Helper: save / load compliance check history
# ---------------------------------------------------------------------------
def _save_compliance_history(report: dict, version_label: str):
    """Append a compliance check run to the history JSON file."""
    history = []
    if COMPLIANCE_HISTORY_PATH.exists():
        try:
            with open(COMPLIANCE_HISTORY_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []

    s = report.get("summary", {})
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version_label": version_label or f"v{len(history) + 1}",
        "total": s.get("total", 0),
        "satisfied": s.get("satisfied", 0),
        "gaps": s.get("gaps", 0),
        "unclear": s.get("unclear", 0),
        "high_risk_gaps": s.get("high_risk_gaps", 0),
    }
    history.append(entry)

    with open(COMPLIANCE_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return entry


def _load_compliance_history() -> list[dict]:
    """Load the compliance check history list."""
    if COMPLIANCE_HISTORY_PATH.exists():
        try:
            with open(COMPLIANCE_HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown('<p class="sidebar-title">BA Intelligence Toolkit</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.markdown('<p class="panel-title">Configuration</p>', unsafe_allow_html=True)

# Provider selection
provider = st.sidebar.radio(
    "LLM Provider",
    options=["DeepSeek", "OpenAI"],
    index=0,
    help="DeepSeek is much cheaper and works great for this use case.",
)

# Set defaults based on provider
if provider == "DeepSeek":
    default_key = os.getenv("LLM_API_KEY", "")
    default_url = "https://api.deepseek.com"
    model_options = ["deepseek-chat", "deepseek-reasoner"]
    default_model = "deepseek-chat"
    key_label = "DeepSeek API Key"
else:
    default_key = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    default_url = ""
    model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    default_model = "gpt-4o-mini"
    key_label = "OpenAI API Key"

# API key input (pre-filled from .env if available)
api_key = st.sidebar.text_input(
    key_label,
    value=st.session_state.get("api_key_input", default_key),
    type="password",
    help=f"Your {provider} API key. Stored only in this session.",
)
if api_key:
    st.session_state.api_key_input = api_key

# Base URL (auto-set, but visible for transparency)
if provider == "DeepSeek":
    st.sidebar.text_input("Base URL", value=default_url, disabled=True)

# Model selection
model = st.sidebar.selectbox(
    "Model",
    options=model_options,
    index=0,
    help=f"{'deepseek-chat' if provider == 'DeepSeek' else 'gpt-4o-mini'} "
         "is recommended for cost and speed.",
)

# Initialize engine
if st.sidebar.button("Initialize AI Engine", type="primary"):
    if not api_key:
        st.sidebar.error(f"Please enter your {provider} API key.")
    else:
        try:
            st.session_state.engine = AIEngine(
                api_key=api_key,
                model=model,
                base_url=default_url if provider == "DeepSeek" else None,
            )
            st.session_state.extractor = RequirementsExtractor(
                st.session_state.engine
            )
            st.session_state.checker = ComplianceGapChecker(
                st.session_state.engine, CHECKLIST_PATH
            )
            st.session_state.rtm_gen = RTMGenerator(st.session_state.engine)
            st.session_state.gap_analyzer = GapAnalyzer(st.session_state.engine)
            st.sidebar.success(f"{provider} engine ready!")
        except Exception as e:
            st.sidebar.error(f"Initialization failed: {e}")

st.sidebar.markdown("---")

# Demo mode toggle
demo_mode = st.sidebar.checkbox(
    "Load Demo Data (no API needed)",
    help="Load pre-computed results for demonstration without API calls.",
)
if demo_mode and st.sidebar.button("Load Demo Results"):
    _load_demo_results()

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<span style="color:#9CA3AF;font-size:0.75rem;">'
    '<strong style="color:#F9FAFB;">Scenario:</strong> Individual retail customer, '
    'digital (non-face-to-face) account opening \u2014 KYC/AML compliance check'
    '</span>',
    unsafe_allow_html=True,
)

# Render usage / cost metrics in sidebar (live or from demo snapshot)
_render_usage()


# ---------------------------------------------------------------------------
# Main content — view selector (tab-style)
# ---------------------------------------------------------------------------
view = st.radio(
    "Select View",
    options=[
        "\U0001F4C4  Extraction",
        "\U0001F6E1  Compliance",
        "\U0001F5C2  RTM & Deps",
        "\U0001F4CA  Process Gaps",
        "\U0001F4E4  Export",
    ],
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("---")


# ---------------------------------------------------------------------------
# View 1: Input & Requirements Extraction
# ---------------------------------------------------------------------------
if view.startswith("\U0001F4C4"):
    st.markdown('<p class="panel-title">Module 01</p>', unsafe_allow_html=True)
    st.header("Requirements Extraction")

    st.markdown(
        '<span style="color:#9CA3AF;">Upload or paste a meeting transcript, BRD draft, '
        "or requirements document. The tool will extract structured requirements, "
        "decisions, actions, risks, assumptions, and constraints.</span>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="panel-title">Input Source</p>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload a text file",
            type=["txt", "pdf"],
            help="Upload a .txt or .pdf file containing the transcript or BRD.",
        )

        if uploaded_file:
            st.session_state.input_text = load_uploaded_file(uploaded_file)
            st.success(f"Loaded: {uploaded_file.name}")

        if st.button("Load Demo Transcript"):
            demo_path = DATA_DIR / "sample_transcript.txt"
            if demo_path.exists():
                st.session_state.input_text = load_text_file(demo_path)
                st.success("Demo transcript loaded.")

        text_input = st.text_area(
            "Or paste text directly",
            value=st.session_state.input_text,
            height=300,
            placeholder="Paste meeting transcript or BRD text here...",
        )
        st.session_state.input_text = text_input

    with col2:
        st.markdown('<p class="panel-title">Extracted Output</p>', unsafe_allow_html=True)

        if st.button("Extract Requirements", type="primary"):
            if not st.session_state.extractor:
                st.error("Please initialize the AI Engine first (sidebar).")
            elif not st.session_state.input_text.strip():
                st.error("Please provide input text first.")
            else:
                with st.spinner("Extracting requirements..."):
                    try:
                        result = st.session_state.extractor.extract(
                            st.session_state.input_text
                        )
                        st.session_state.extraction_result = result
                        st.success(
                            f"Extracted {len(result.get('requirements', []))} "
                            f"requirements."
                        )
                    except Exception as e:
                        st.error(f"Extraction failed: {e}")

        result = st.session_state.extraction_result
        if result:
            reqs = result.get("requirements", [])

            # Metric cards
            m1, m2, m3 = st.columns(3)
            m1.metric("Requirements", len(reqs))
            high_count = sum(1 for r in reqs if r.get("priority") == "High")
            m2.metric("High Priority", high_count)
            reg_count = sum(1 for r in reqs if r.get("type") == "Regulatory")
            m3.metric("Regulatory", reg_count)

            if reqs:
                import pandas as pd
                df = pd.DataFrame(reqs)
                st.dataframe(
                    df[["req_id", "title", "type", "priority"]],
                    use_container_width=True,
                )

            for label, key in [
                ("Decisions", "decisions"),
                ("Actions", "actions"),
                ("Risks", "risks"),
                ("Assumptions", "assumptions"),
                ("Constraints", "constraints"),
            ]:
                items = result.get(key, [])
                if items:
                    with st.expander(f"{label} ({len(items)})"):
                        for item in items:
                            st.markdown(f"- {item}")


# ---------------------------------------------------------------------------
# View 2: Compliance Gap Reasoning
# ---------------------------------------------------------------------------
elif view.startswith("\U0001F6E1"):
    st.markdown('<p class="panel-title">Module 02</p>', unsafe_allow_html=True)
    st.header("Compliance Gap Reasoning")

    st.markdown(
        '<span style="color:#9CA3AF;">The tool checks the BRD against a structured '
        "<strong style=\"color:#F9FAFB;\">Compliance Obligation Checklist</strong> "
        "\u2014 not by matching keywords, but by reasoning about whether each "
        "obligation is covered by the requirements.</span>",
        unsafe_allow_html=True,
    )

    st.info(
        "**Checklist scope:** Individual retail customer, digital "
        "(non-face-to-face) account opening \u2014 KYC/AML. "
        "Based on MLR 2017, JMLSG Guidance, FCA FG17-6, UK GDPR, "
        "FCA Consumer Duty."
    )

    # Show checklist overview
    if st.session_state.checker:
        with st.expander("View Compliance Obligation Checklist"):
            for o in st.session_state.checker.obligations:
                depth_badge = (
                    ' <span style="color:#EF4444;font-weight:700;">[DEEP]</span>'
                    if o.get("depth") == "deep" else ""
                )
                st.markdown(
                    f"**{o['obligation_id']}** ({o['category']}) "
                    f"\u2014 *{o.get('severity', 'medium').upper()}*{depth_badge}",
                    unsafe_allow_html=True,
                )
                st.markdown(f"  - **Obligation:** {o['obligation']}")
                st.markdown(f"  - **Source:** {o['source']}")
                st.markdown("")

    # BRD version label + Run compliance check
    col_ver, col_btn, col_info = st.columns([1, 1, 2])
    with col_ver:
        version_label = st.text_input(
            "BRD Version Label",
            value=st.session_state.brd_version_label,
            placeholder="e.g. v1.0-draft",
            help="Label this BRD revision so you can track gap count "
                 "changes across versions in the history table below.",
        )
        st.session_state.brd_version_label = version_label

    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Run Compliance Check", type="primary"):
            if not st.session_state.checker:
                st.error("Please initialize the AI Engine first (sidebar).")
            elif not st.session_state.input_text.strip():
                st.error("Please extract requirements first (View 1).")
            else:
                with st.spinner(
                    "Reasoning through compliance obligations... "
                    "This may take 30-60 seconds."
                ):
                    try:
                        report = st.session_state.checker.check(
                            st.session_state.input_text
                        )
                        st.session_state.compliance_report = report

                        # Auto-save to compliance history
                        try:
                            _save_compliance_history(
                                report,
                                st.session_state.brd_version_label,
                            )
                        except Exception:
                            pass

                        st.success(
                            f"Check complete: {report['summary']['gaps']} gaps, "
                            f"{report['summary']['satisfied']} satisfied, "
                            f"{report['summary']['unclear']} unclear."
                        )
                    except Exception as e:
                        st.error(f"Compliance check failed: {e}")

    # Display results
    report = st.session_state.compliance_report
    if report:
        s = report["summary"]

        # Summary metrics — Bloomberg-style number cards
        st.markdown('<p class="panel-title">Summary Metrics</p>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Obligations", s["total"])
        col2.metric("Satisfied", s["satisfied"])
        col3.metric("Gaps", s["gaps"])
        col4.metric("High-Risk Gaps", s["high_risk_gaps"])

        st.markdown("---")

        # Heatmap
        fig_heat = create_compliance_heatmap(report)
        fig_heat = _dark_plotly_layout(fig_heat, "Compliance Obligation Check Results")
        # Override bar colors for dark theme
        fig_heat.update_traces(
            textfont=dict(color="#F9FAFB"),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # Gaps section
        st.markdown('<p class="panel-title">\u26A0 Identified Gaps</p>', unsafe_allow_html=True)
        if report["gaps"]:
            for gap in report["gaps"]:
                severity = "high"
                if st.session_state.checker:
                    detail = st.session_state.checker.get_obligation_detail(
                        gap.get("obligation_id", "")
                    )
                    if detail:
                        severity = detail.get("severity", "medium")

                severity_colors = {
                    "high": "#EF4444",
                    "medium": "#F59E0B",
                    "low": "#10B981",
                }
                severity_labels = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}
                color = severity_colors.get(severity, "#9CA3AF")
                label = severity_labels.get(severity, "UNKNOWN")

                with st.expander(
                    f"{gap.get('obligation_id', '?')} \u2014 {label} RISK GAP"
                ):
                    st.markdown(
                        f'<div style="border-left:3px solid {color};'
                        f'padding-left:16px;margin:-8px -12px 0 -12px;padding:12px 16px;">',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Status:** `{gap.get('status', '')}`")
                    st.markdown(f"**Reasoning:** {gap.get('reasoning', '')}")
                    st.markdown(
                        f"**Consequence if gap:** "
                        f"{gap.get('consequence_if_gap', '')}"
                    )
                    st.markdown(
                        f"**Suggested control:** "
                        f"{gap.get('suggested_control', '')}"
                    )

                    if st.session_state.checker:
                        detail = st.session_state.checker.get_obligation_detail(
                            gap.get("obligation_id", "")
                        )
                        if detail:
                            st.markdown("---")
                            st.markdown(
                                f'<span style="color:#9CA3AF;font-size:0.8rem;">'
                                f"Source: {detail.get('source', '')}</span>",
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f'<span style="color:#9CA3AF;font-size:0.8rem;">'
                                f"Obligation: {detail.get('obligation', '')}</span>",
                                unsafe_allow_html=True,
                            )
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.success("No gaps identified! All obligations are satisfied.")

        # Unclear section
        if report["unclear"]:
            st.markdown('<p class="panel-title">\u2754 Unclear (Requires Manual Review)</p>', unsafe_allow_html=True)
            for item in report["unclear"]:
                with st.expander(
                    f"{item.get('obligation_id', '?')} \u2014 Unclear"
                ):
                    st.markdown(f"**Reasoning:** {item.get('reasoning', '')}")

        # Satisfied section
        if report["satisfied"]:
            st.markdown('<p class="panel-title">\u2705 Satisfied Obligations</p>', unsafe_allow_html=True)
            for item in report["satisfied"]:
                st.markdown(
                    f'- **{item.get("obligation_id", "?")}**: '
                    f"{item.get('reasoning', '')[:120]}..."
                )

    # --- Compliance Check History ---
    history = _load_compliance_history()
    if history:
        st.markdown("---")
        st.markdown('<p class="panel-title">\U0001F4CA Check History (Gap Trend)</p>', unsafe_allow_html=True)
        st.markdown(
            '<span style="color:#9CA3AF;font-size:0.85rem;">'
            "Each compliance check run is automatically saved below. "
            "Use this to track how the gap count changes as the BRD is revised."
            "</span>",
            unsafe_allow_html=True,
        )
        import pandas as pd
        hist_rows = []
        for i, h in enumerate(history, 1):
            ts = h.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts_display = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                ts_display = ts[:16]
            hist_rows.append({
                "#": i,
                "Version": h.get("version_label", ""),
                "Time": ts_display,
                "Total": h.get("total", ""),
                "Satisfied": h.get("satisfied", ""),
                "Gaps": h.get("gaps", ""),
                "High-Risk": h.get("high_risk_gaps", ""),
            })
        df_hist = pd.DataFrame(hist_rows)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)

        # Gap trend chart
        if len(hist_rows) >= 2:
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                x=[r["Version"] for r in hist_rows],
                y=[r["Gaps"] for r in hist_rows],
                mode="lines+markers+text",
                text=[str(r["Gaps"]) for r in hist_rows],
                textposition="top center",
                name="Gaps",
                line=dict(color="#EF4444", width=2),
                marker=dict(size=8, color="#EF4444"),
                textfont=dict(color="#F9FAFB"),
            ))
            fig_hist.add_trace(go.Scatter(
                x=[r["Version"] for r in hist_rows],
                y=[r["High-Risk"] for r in hist_rows],
                mode="lines+markers",
                name="High-Risk Gaps",
                line=dict(color="#F59E0B", width=2, dash="dash"),
                marker=dict(size=6, color="#F59E0B"),
            ))
            fig_hist = _dark_plotly_layout(fig_hist, "Gap Count Trend Across BRD Versions")
            fig_hist.update_layout(
                xaxis_title="BRD Version",
                yaxis_title="Count",
                height=300,
                legend=dict(font=dict(color="#9CA3AF")),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        if st.button("Clear History", type="secondary"):
            with open(COMPLIANCE_HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump([], f)
            st.rerun()


# ---------------------------------------------------------------------------
# View 3: RTM & Dependency Analysis
# ---------------------------------------------------------------------------
elif view.startswith("\U0001F5C2"):
    st.markdown('<p class="panel-title">Module 03</p>', unsafe_allow_html=True)
    st.header("RTM & Dependency Analysis")

    st.markdown(
        '<span style="color:#9CA3AF;">Generate a Requirements Traceability Matrix '
        "(RTM) and visualize the dependency graph between requirements.</span>",
        unsafe_allow_html=True,
    )

    if st.button("Generate RTM", type="primary"):
        if not st.session_state.rtm_gen:
            st.error("Please initialize the AI Engine first (sidebar).")
        elif not st.session_state.extraction_result:
            st.error("Please extract requirements first (Module 01).")
        else:
            with st.spinner("Generating RTM..."):
                try:
                    reqs = st.session_state.extraction_result.get(
                        "requirements", []
                    )
                    rtm = st.session_state.rtm_gen.generate(reqs)
                    st.session_state.rtm_result = rtm
                    st.success("RTM generated!")
                except Exception as e:
                    st.error(f"RTM generation failed: {e}")

    rtm = st.session_state.rtm_result
    if rtm:
        # Dependency graph
        st.markdown('<p class="panel-title">Dependency Graph</p>', unsafe_allow_html=True)
        from modules.rtm import RTMGenerator as RTM
        edges = rtm.get("dependency_graph", [])
        G = RTM.build_dependency_graph(edges)
        if len(G.nodes) > 0:
            fig = RTM.visualize_graph(G)
            fig = _dark_plotly_layout(fig, "Requirement Dependency Graph")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No dependencies identified between requirements.")

        # Impact analysis
        if len(G.nodes) > 0:
            st.markdown('<p class="panel-title">Impact Analysis</p>', unsafe_allow_html=True)
            selected = st.selectbox(
                "Select a requirement to analyze impact:",
                options=list(G.nodes),
            )
            if selected:
                impact = RTM.analyze_impact(G, selected)
                st.markdown(f"**Changed requirement:** `{impact['changed']}`")
                st.markdown(
                    f"**Downstream impact (depends on this):** "
                    f"{', '.join(impact['impacted_downstream']) or 'None'}"
                )
                st.markdown(
                    f"**Upstream dependencies (this depends on):** "
                    f"{', '.join(impact['impacted_upstream']) or 'None'}"
                )
                st.metric(
                    "Total Impacted Requirements", impact["total_impacted"]
                )

        # RTM table
        st.markdown('<p class="panel-title">Requirements Traceability Matrix</p>', unsafe_allow_html=True)
        import pandas as pd
        entries = rtm.get("rtm_entries", [])
        if entries:
            df = pd.DataFrame(entries)
            st.dataframe(df, use_container_width=True)


# ---------------------------------------------------------------------------
# View 4: Process Gap Analysis
# ---------------------------------------------------------------------------
elif view.startswith("\U0001F4CA"):
    st.markdown('<p class="panel-title">Module 04</p>', unsafe_allow_html=True)
    st.header("Process Gap Analysis")

    st.markdown(
        '<span style="color:#9CA3AF;">Compare As-Is and To-Be processes to identify '
        "gaps, bottlenecks, and improvement opportunities.</span>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="panel-title">As-Is Process</p>', unsafe_allow_html=True)
        as_is_file = st.file_uploader(
            "Upload As-Is process", type=["txt"], key="as_is_upload"
        )
        if as_is_file:
            st.session_state.as_is_text = load_uploaded_file(as_is_file)

        if st.button("Load Demo As-Is"):
            path = DATA_DIR / "as_is_process.txt"
            if path.exists():
                st.session_state.as_is_text = load_text_file(path)

        st.session_state.as_is_text = st.text_area(
            "As-Is process text",
            value=st.session_state.as_is_text,
            height=250,
        )

    with col2:
        st.markdown('<p class="panel-title">To-Be Process</p>', unsafe_allow_html=True)
        to_be_file = st.file_uploader(
            "Upload To-Be process", type=["txt"], key="to_be_upload"
        )
        if to_be_file:
            st.session_state.to_be_text = load_uploaded_file(to_be_file)

        if st.button("Load Demo To-Be"):
            path = DATA_DIR / "to_be_process.txt"
            if path.exists():
                st.session_state.to_be_text = load_text_file(path)

        st.session_state.to_be_text = st.text_area(
            "To-Be process text",
            value=st.session_state.to_be_text,
            height=250,
        )

    if st.button("Analyze Gaps", type="primary"):
        if not st.session_state.gap_analyzer:
            st.error("Please initialize the AI Engine first (sidebar).")
        elif not st.session_state.as_is_text.strip() or not st.session_state.to_be_text.strip():
            st.error("Please provide both As-Is and To-Be process text.")
        else:
            with st.spinner("Analyzing process gaps..."):
                try:
                    result = st.session_state.gap_analyzer.analyze(
                        st.session_state.as_is_text,
                        st.session_state.to_be_text,
                    )
                    st.session_state.gap_result = result
                    st.success(
                        f"Found {len(result.get('gaps', []))} gaps."
                    )
                except Exception as e:
                    st.error(f"Gap analysis failed: {e}")

    gap_result = st.session_state.gap_result
    if gap_result:
        # Metrics
        st.markdown('<p class="panel-title">Process Metrics</p>', unsafe_allow_html=True)
        metrics = gap_result.get("metrics", {})
        if metrics:
            col1, col2, col3 = st.columns(3)
            col1.metric("As-Is Time", metrics.get("as_is_time", "N/A"))
            col2.metric("To-Be Time", metrics.get("to_be_time", "N/A"))
            col3.metric("FTE Change", metrics.get("fte_change", "N/A"))

        # Priority matrix
        fig_pm = create_gap_priority_matrix(gap_result)
        fig_pm = _dark_plotly_layout(fig_pm, "Gap Priority Matrix (Impact vs Difficulty)")
        fig_pm.update_traces(
            marker=dict(size=15, color="#3B82F6", line=dict(color="#00D4FF", width=1)),
            textfont=dict(color="#F9FAFB"),
        )
        st.plotly_chart(fig_pm, use_container_width=True)

        # Gaps table
        st.markdown('<p class="panel-title">Identified Gaps</p>', unsafe_allow_html=True)
        import pandas as pd
        gaps = gap_result.get("gaps", [])
        if gaps:
            df = pd.DataFrame(gaps)
            st.dataframe(df, use_container_width=True)

        # Risks
        risks = gap_result.get("risks", [])
        if risks:
            st.markdown('<p class="panel-title">Transformation Risks</p>', unsafe_allow_html=True)
            for risk in risks:
                st.markdown(f"- \u26A0 {risk}")


# ---------------------------------------------------------------------------
# View 5: Export Report
# ---------------------------------------------------------------------------
elif view.startswith("\U0001F4E4"):
    st.markdown('<p class="panel-title">Module 05</p>', unsafe_allow_html=True)
    st.header("Export Report")

    st.markdown(
        '<span style="color:#9CA3AF;">Export all results to a single Excel file.</span>',
        unsafe_allow_html=True,
    )

    # Check what data is available
    has_data = False
    if st.session_state.extraction_result:
        st.markdown("\u2705 Requirements extraction results available")
        has_data = True
    else:
        st.markdown("\u274C No requirements extraction results")

    if st.session_state.compliance_report:
        st.markdown("\u2705 Compliance gap check results available")
        has_data = True
    else:
        st.markdown("\u274C No compliance gap check results")

    if st.session_state.rtm_result:
        st.markdown("\u2705 RTM results available")
        has_data = True
    else:
        st.markdown("\u274C No RTM results")

    if st.session_state.gap_result:
        st.markdown("\u2705 Process gap analysis results available")
        has_data = True
    else:
        st.markdown("\u274C No process gap analysis results")

    st.markdown("---")

    # --- Save demo snapshot ---
    st.markdown('<p class="panel-title">Save Demo Snapshot</p>', unsafe_allow_html=True)
    st.markdown(
        '<span style="color:#9CA3AF;font-size:0.85rem;">'
        "Save the current session results to <code style='color:#00D4FF;'>"
        "data/demo_results.json</code>. This enables offline Demo Mode without "
        "API calls \u2014 useful for interviews or demonstrations where network "
        "access is unreliable."
        "</span>",
        unsafe_allow_html=True,
    )
    if st.button("Save Current Results as Demo Snapshot", type="secondary"):
        if not has_data:
            st.warning("No results to save. Run the analysis first.")
        else:
            try:
                path = _save_demo_results()
                st.success(f"Demo snapshot saved to: {path}")
            except Exception as e:
                st.error(f"Failed to save snapshot: {e}")

    st.markdown("---")

    if has_data and st.button("Generate Excel Report", type="primary"):
        excel_data = export_to_excel(
            requirements=(
                st.session_state.extraction_result.get("requirements", [])
                if st.session_state.extraction_result else None
            ),
            compliance_report=st.session_state.compliance_report,
            rtm_data=st.session_state.rtm_result,
            gap_analysis=st.session_state.gap_result,
        )
        st.download_button(
            label="Download Excel Report",
            data=excel_data,
            file_name="ba_intelligence_toolkit_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.success("Report ready for download!")
