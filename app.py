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
# Editorial CSS — The Vault inspired
# ---------------------------------------------------------------------------
VAULT_CSS = """
<style>
/* ── Root variables ─────────────────────────────────────────────── */
:root {
    --bg: #FAF9F7;
    --surface: #F4F1ED;
    --border: #E5E0D8;
    --text-primary: #1A1A1A;
    --text-secondary: #6B6560;
    --text-caption: #9C9490;
    --accent: #3D2B1F;
    --success: #4A7C59;
    --warning: #9C7A3C;
    --danger: #8B3A3A;
    --font-serif: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Palatino, 'Source Serif Pro', serif;
    --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

/* ── Global background ──────────────────────────────────────────── */
.stApp {
    background-color: var(--bg);
    color: var(--text-primary);
    font-family: var(--font-sans);
}

/* ── Remove default Streamlit padding for cleaner look ──────────── */
.block-container {
    padding-top: 2.5rem !important;
    max-width: 1100px;
}

/* ── Headings: serif, light weight ─────────────────────────────── */
h1, h2, h3 {
    font-family: var(--font-serif) !important;
    font-weight: 300 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.01em;
}
h1 {
    font-size: 2.2rem !important;
    margin-bottom: 0.3rem;
}
h2 {
    font-size: 1.6rem !important;
}
h3 {
    font-size: 1.2rem !important;
}

/* ── Module label (caption above header) ───────────────────────── */
.module-label {
    font-family: var(--font-sans);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--text-caption);
    font-weight: 500;
    margin-bottom: 0.2rem;
}

/* ── Section caption ────────────────────────────────────────────── */
.section-caption {
    font-family: var(--font-sans);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--text-caption);
    font-weight: 500;
    margin-top: 2rem;
    margin-bottom: 0.6rem;
}

/* ── Body text: generous line height ───────────────────────────── */
p, li, span {
    line-height: 1.7;
}
.stMarkdown p {
    color: var(--text-secondary);
    font-size: 0.92rem;
}

/* ── Sidebar ────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: var(--surface);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-primary) !important;
}

/* ── Tool name in sidebar ──────────────────────────────────────── */
.sidebar-title {
    font-family: var(--font-serif) !important;
    color: var(--accent) !important;
    font-weight: 400 !important;
    font-size: 1.3rem !important;
    letter-spacing: -0.01em;
}
.sidebar-subtitle {
    font-family: var(--font-sans);
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--text-caption);
    margin-top: 0.2rem;
}

/* ── Sidebar labels ─────────────────────────────────────────────── */
.sidebar-label {
    font-family: var(--font-sans);
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--text-caption);
    font-weight: 500;
    margin-top: 1.2rem;
    margin-bottom: 0.4rem;
}

/* ── Top navigation bar ────────────────────────────────────────── */
.top-nav {
    display: flex;
    gap: 2.5rem;
    padding: 0 0 1.2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.top-nav-item {
    font-family: var(--font-sans);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--text-caption);
    font-weight: 500;
    cursor: default;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid transparent;
}
.top-nav-item.active {
    color: var(--text-primary);
    border-bottom-color: var(--accent);
}

/* ── Metric cards: large serif numbers ─────────────────────────── */
.metric-block {
    text-align: left;
    padding: 1.2rem 0;
}
.metric-number {
    font-family: var(--font-serif);
    font-size: 2.8rem;
    font-weight: 300;
    color: var(--text-primary);
    line-height: 1;
    margin-bottom: 0.3rem;
}
.metric-label {
    font-family: var(--font-sans);
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--text-caption);
    font-weight: 500;
}

/* ── StMetric override (fallback) ──────────────────────────────── */
div[data-testid="stMetric"] {
    background-color: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 1rem 0 !important;
    box-shadow: none !important;
}
div[data-testid="stMetric"] label {
    color: var(--text-caption) !important;
    font-size: 0.62rem !important;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-weight: 500;
    font-family: var(--font-sans) !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-family: var(--font-serif) !important;
    font-size: 2.4rem !important;
    font-weight: 300;
}

/* ── Buttons: outlined or text-only ────────────────────────────── */
.stButton > button[kind="primary"] {
    background-color: transparent !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 2px !important;
    text-transform: uppercase;
    font-weight: 500;
    letter-spacing: 0.12em;
    font-size: 0.72rem;
    font-family: var(--font-sans);
    padding: 0.5rem 1.4rem;
    transition: all 0.2s ease;
}
.stButton > button[kind="primary"]:hover {
    background-color: var(--accent) !important;
    color: var(--bg) !important;
    border-color: var(--accent) !important;
}
.stButton > button[kind="secondary"] {
    background-color: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    text-transform: uppercase;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    font-family: var(--font-sans);
    padding: 0.45rem 1.2rem;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--text-secondary) !important;
    color: var(--text-primary) !important;
}

/* ── Text inputs: minimal, thin border, warm bg ────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-sans);
    font-size: 0.9rem;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: var(--text-caption) !important;
}

/* ── Selectbox ──────────────────────────────────────────────────── */
.stSelectbox > div > div {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
}

/* ── Dataframes: editorial table ───────────────────────────────── */
.stDataFrame {
    border: none !important;
    border-radius: 0 !important;
}
.stDataFrame [data-testid="stDataFrame"] {
    background-color: transparent !important;
}
/* Table header */
.stDataFrame th {
    font-family: var(--font-sans) !important;
    font-size: 0.65rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-caption) !important;
    font-weight: 500;
    border-bottom: 1px solid var(--border) !important;
    background-color: transparent !important;
}
.stDataFrame td {
    border-bottom: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    font-size: 0.88rem !important;
}
.stDataFrame tr:hover td {
    background-color: var(--surface) !important;
}

/* ── Expanders (gap cards) ──────────────────────────────────────── */
.streamlit-expanderHeader {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 1px solid var(--border) !important;
    border-radius: 0 !important;
    font-family: var(--font-sans);
    font-size: 0.88rem;
    color: var(--text-primary);
    padding: 0.8rem 0;
}
.streamlit-expanderContent {
    background-color: transparent !important;
    border: none !important;
    border-bottom: 1px solid var(--border) !important;
    border-radius: 0 !important;
    padding: 0.5rem 0 1rem 0;
}

/* ── Severity indicators: thin vertical bar ────────────────────── */
.severity-bar {
    display: inline-block;
    width: 3px;
    height: 1em;
    vertical-align: middle;
    margin-right: 0.6rem;
    border-radius: 0;
}
.severity-bar.high { background-color: var(--danger); }
.severity-bar.medium { background-color: var(--warning); }
.severity-bar.low { background-color: var(--success); }

/* ── Severity dot ───────────────────────────────────────────────── */
.severity-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    vertical-align: middle;
    margin-right: 0.5rem;
}
.severity-dot.high { background-color: var(--danger); }
.severity-dot.medium { background-color: var(--warning); }
.severity-dot.low { background-color: var(--success); }

/* ── Gap detail content ─────────────────────────────────────────── */
.gap-detail {
    padding: 0.5rem 0 0.5rem 1rem;
    border-left: 2px solid var(--border);
}
.gap-detail .field-label {
    font-family: var(--font-sans);
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--text-caption);
    font-weight: 500;
    margin-top: 0.6rem;
    margin-bottom: 0.15rem;
}
.gap-detail .field-value {
    font-family: var(--font-sans);
    font-size: 0.9rem;
    color: var(--text-primary);
    line-height: 1.6;
}
.gap-detail .source-line {
    font-family: var(--font-sans);
    font-size: 0.78rem;
    color: var(--text-secondary);
    margin-top: 0.3rem;
}

/* ── Alerts ─────────────────────────────────────────────────────── */
.stAlert {
    background-color: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
}
.stAlert [data-testid="stAlertContent"] {
    color: var(--text-secondary) !important;
    font-size: 0.88rem;
}

/* ── Info box ───────────────────────────────────────────────────── */
.stAlert [data-testid="stAlertContent"] p {
    color: var(--text-secondary) !important;
    font-size: 0.88rem;
    line-height: 1.6;
}

/* ── Checkboxes ─────────────────────────────────────────────────── */
.stCheckbox label {
    color: var(--text-secondary) !important;
    font-size: 0.88rem;
}
.stCheckbox label p {
    color: var(--text-secondary) !important;
}

/* ── File uploader ──────────────────────────────────────────────── */
.stFileUploader {
    border: 1px dashed var(--border) !important;
    border-radius: 2px;
    background-color: var(--surface);
}

/* ── Spinner ────────────────────────────────────────────────────── */
.stSpinner > div {
    color: var(--accent) !important;
}

/* ── Divider ────────────────────────────────────────────────────── */
hr, .stMarkdown hr {
    border-color: var(--border) !important;
    border-top: 1px solid var(--border) !important;
    margin: 2rem 0;
}

/* ── Radio (view selector) — styled as top nav ─────────────────── */
/* Hide the actual radio circles */
div[data-testid="stRadio"] input[type="radio"] {
    display: none !important;
}

/* Radio group laid out horizontally */
div[data-testid="stRadio"] > div {
    display: flex !important;
    flex-direction: row !important;
    gap: 2.5rem !important;
    padding: 0 0 1.2rem 0 !important;
    border-bottom: 1px solid var(--border) !important;
    margin-bottom: 2rem !important;
    background-color: transparent !important;
}

/* Each label is a nav item */
div[data-testid="stRadio"] label {
    font-family: var(--font-sans) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.16em !important;
    color: var(--text-caption) !important;
    font-weight: 500 !important;
    padding-bottom: 0.5rem !important;
    border-bottom: 2px solid transparent !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: color 0.2s ease, border-color 0.2s ease !important;
}
div[data-testid="stRadio"] label:hover {
    color: var(--text-primary) !important;
}

/* Selected item */
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:last-child {
    color: var(--text-primary) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* Streamlit sometimes wraps the checked label differently; target checked state */
div[data-testid="stRadio"] input[type="radio"]:checked + div label,
div[data-testid="stRadio"] input[type="radio"]:checked + label {
    color: var(--text-primary) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* ── Plotly chart container ─────────────────────────────────────── */
.stPlotlyChart {
    margin-top: 0.5rem;
}

/* ── Footer ─────────────────────────────────────────────────────── */
.footer {
    margin-top: 5rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border);
    text-align: center;
}
.footer-line-1 {
    font-family: var(--font-sans);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    color: var(--text-caption);
    font-weight: 500;
}
.footer-line-2 {
    font-family: var(--font-sans);
    font-size: 0.78rem;
    color: var(--text-caption);
    margin-top: 0.4rem;
    font-weight: 400;
    letter-spacing: 0.02em;
}

/* ── Usage block in sidebar ─────────────────────────────────────── */
.usage-row {
    font-family: var(--font-sans);
    font-size: 0.78rem;
    color: var(--text-secondary);
    margin-bottom: 0.3rem;
}
.usage-label {
    color: var(--text-caption);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

/* ── Checkbox list items ────────────────────────────────────────── */
.stMarkdown ul li {
    color: var(--text-secondary);
}

/* ── Data table styling for pandas dataframes ──────────────────── */
table.dataframe {
    border: none !important;
}
table.dataframe th {
    font-family: var(--font-sans) !important;
    font-size: 0.65rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-caption) !important;
    font-weight: 500;
    border-bottom: 1px solid var(--border) !important;
    background-color: transparent !important;
    text-align: left;
    padding: 0.6rem 0.8rem !important;
}
table.dataframe td {
    border-bottom: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    font-size: 0.88rem !important;
    padding: 0.6rem 0.8rem !important;
}

/* ── Download button ────────────────────────────────────────────── */
.stDownloadButton > button {
    background-color: transparent !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 2px !important;
    text-transform: uppercase;
    font-weight: 500;
    letter-spacing: 0.12em;
    font-size: 0.72rem;
    font-family: var(--font-sans);
}
.stDownloadButton > button:hover {
    background-color: var(--accent) !important;
    color: var(--bg) !important;
}
</style>
"""
st.markdown(VAULT_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Plotly light theme helper
# ---------------------------------------------------------------------------
def _light_plotly_layout(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply light editorial theme to a Plotly figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(color="#1A1A1A", size=14, family="serif")),
        paper_bgcolor="#FAF9F7",
        plot_bgcolor="#FAF9F7",
        font=dict(color="#6B6560", family="sans-serif", size=12),
        xaxis=dict(gridcolor="#E5E0D8", zerolinecolor="#E5E0D8", linecolor="#E5E0D8"),
        yaxis=dict(gridcolor="#E5E0D8", zerolinecolor="#E5E0D8", linecolor="#E5E0D8"),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def _render_footer():
    """Render the editorial footer signature on every page."""
    st.markdown(
        '<div class="footer">'
        '<div class="footer-line-1">'
        'FANQIAO (FAYE) XU &mdash; LONDON, 2026'
        '</div>'
        '<div class="footer-line-2">'
        'Designed as a portfolio project demonstrating BA methodology '
        'applied to UK KYC/AML compliance.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


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
if "current_view" not in st.session_state:
    st.session_state.current_view = 0


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
        st.sidebar.success("Demo data loaded.")
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

    st.sidebar.markdown('<div class="sidebar-label">Usage</div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        f'<div class="usage-row">'
        f'<span class="usage-label">Model</span> &nbsp; {usage.get("model", "N/A")}'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        f'<div class="usage-row">'
        f'<span class="usage-label">Calls</span> &nbsp; {usage.get("calls", 0)} &nbsp;&nbsp;'
        f'<span class="usage-label">Tokens</span> &nbsp; {usage.get("total_tokens", 0):,}'
        f'</div>',
        unsafe_allow_html=True,
    )
    cost = usage.get("cost_cny", {})
    if cost and cost.get("total_cost") is not None:
        st.sidebar.markdown(
            f'<div class="usage-row">'
            f'<span class="usage-label">Est. Cost</span> &nbsp; \u00a5{cost["total_cost"]:.4f}'
            f'</div>',
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
# Helper: render metric block (large serif number + small label)
# ---------------------------------------------------------------------------
def _metric_block(number, label: str):
    """Render a large serif number with a small uppercase label beneath."""
    st.markdown(
        f'<div class="metric-block">'
        f'<div class="metric-number">{number}</div>'
        f'<div class="metric-label">{label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    '<p class="sidebar-title">BA Intelligence Toolkit</p>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<p class="sidebar-subtitle">Compliance Gap Reasoning</p>',
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

st.sidebar.markdown('<div class="sidebar-label">Configuration</div>', unsafe_allow_html=True)

# Provider selection
provider = st.sidebar.radio(
    "LLM Provider",
    options=["DeepSeek", "OpenAI"],
    index=0,
    help="DeepSeek is much cheaper and works great for this use case.",
    label_visibility="collapsed",
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
            st.sidebar.success(f"{provider} engine ready.")
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
    '<div class="sidebar-label">Scenario</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<p style="font-size:0.82rem;color:#6B6560;line-height:1.6;">'
    'Individual retail customer, digital (non-face-to-face) '
    'account opening \u2014 KYC/AML compliance check'
    '</p>',
    unsafe_allow_html=True,
)

# Render usage / cost metrics in sidebar (live or from demo snapshot)
_render_usage()


# ---------------------------------------------------------------------------
# Top navigation bar
# ---------------------------------------------------------------------------
nav_labels = [
    "Extraction",
    "Compliance",
    "RTM & Deps",
    "Process Gaps",
    "Export",
]

# Radio serves as the functional top navigation; CSS styles the labels as nav items
view = st.radio(
    "Select View",
    options=range(len(nav_labels)),
    format_func=lambda i: nav_labels[i],
    horizontal=True,
    label_visibility="collapsed",
)
st.session_state.current_view = view


# ---------------------------------------------------------------------------
# View 1: Input & Requirements Extraction
# ---------------------------------------------------------------------------
if view == 0:
    st.markdown('<p class="module-label">Module 01</p>', unsafe_allow_html=True)
    st.markdown("## Requirements Extraction")

    st.markdown(
        "Upload or paste a meeting transcript, BRD draft, or requirements "
        "document. The tool will extract structured requirements, decisions, "
        "actions, risks, assumptions, and constraints."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-caption">Input Source</p>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload a text file",
            type=["txt", "pdf"],
            help="Upload a .txt or .pdf file containing the transcript or BRD.",
            label_visibility="collapsed",
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
            label_visibility="collapsed",
        )
        st.session_state.input_text = text_input

    with col2:
        st.markdown('<p class="section-caption">Extracted Output</p>', unsafe_allow_html=True)

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

            # Large typographic metrics
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                _metric_block(len(reqs), "Requirements")
            with mc2:
                high_count = sum(1 for r in reqs if r.get("priority") == "High")
                _metric_block(high_count, "High Priority")
            with mc3:
                reg_count = sum(1 for r in reqs if r.get("type") == "Regulatory")
                _metric_block(reg_count, "Regulatory")

            if reqs:
                import pandas as pd
                df = pd.DataFrame(reqs)
                st.dataframe(
                    df[["req_id", "title", "type", "priority"]],
                    use_container_width=True,
                    hide_index=True,
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
elif view == 1:
    st.markdown('<p class="module-label">Module 02</p>', unsafe_allow_html=True)
    st.markdown("## Compliance Gap Reasoning")

    st.markdown(
        "The tool checks the BRD against a structured "
        "**Compliance Obligation Checklist** \u2014 not by matching keywords, "
        "but by reasoning about whether each obligation is covered by the "
        "requirements."
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
                st.markdown(
                    f"**{o['obligation_id']}** ({o['category']}) "
                    f"\u2014 *{o.get('severity', 'medium').upper()}*",
                )
                st.markdown(f"- **Obligation:** {o['obligation']}")
                st.markdown(f"- **Source:** {o['source']}")
                st.markdown("")

    # BRD version label + Run compliance check
    col_ver, col_btn = st.columns([1, 1])
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
                st.error("Please extract requirements first (Module 01).")
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

        # Summary metrics — large serif numbers
        st.markdown('<p class="section-caption">Summary</p>', unsafe_allow_html=True)
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            _metric_block(s["total"], "Total Obligations")
        with mc2:
            _metric_block(s["satisfied"], "Satisfied")
        with mc3:
            _metric_block(s["gaps"], "Gaps")
        with mc4:
            _metric_block(s["high_risk_gaps"], "High-Risk Gaps")

        st.markdown("---")

        # Heatmap
        fig_heat = create_compliance_heatmap(report)
        fig_heat = _light_plotly_layout(fig_heat, "Compliance Obligation Check Results")
        fig_heat.update_traces(
            textfont=dict(color="#1A1A1A"),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        # Gaps section
        st.markdown('<p class="section-caption">Identified Gaps</p>', unsafe_allow_html=True)
        if report["gaps"]:
            for gap in report["gaps"]:
                severity = "high"
                if st.session_state.checker:
                    detail = st.session_state.checker.get_obligation_detail(
                        gap.get("obligation_id", "")
                    )
                    if detail:
                        severity = detail.get("severity", "medium")

                severity_labels = {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"}
                label = severity_labels.get(severity, "UNKNOWN")

                with st.expander(
                    f"{gap.get('obligation_id', '?')} \u2014 {label} RISK"
                ):
                    st.markdown(
                        f'<div class="gap-detail">'
                        f'<div class="field-label">Status</div>'
                        f'<div class="field-value">{gap.get("status", "")}</div>'
                        f'<div class="field-label">Reasoning</div>'
                        f'<div class="field-value">{gap.get("reasoning", "")}</div>'
                        f'<div class="field-label">Consequence if gap</div>'
                        f'<div class="field-value">{gap.get("consequence_if_gap", "")}</div>'
                        f'<div class="field-label">Suggested Control</div>'
                        f'<div class="field-value">{gap.get("suggested_control", "")}</div>',
                        unsafe_allow_html=True,
                    )

                    if st.session_state.checker:
                        detail = st.session_state.checker.get_obligation_detail(
                            gap.get("obligation_id", "")
                        )
                        if detail:
                            st.markdown(
                                f'<div class="source-line">'
                                f'Source: {detail.get("source", "")} &nbsp;&nbsp;|&nbsp;&nbsp; '
                                f'Obligation: {detail.get("obligation", "")}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.success("No gaps identified. All obligations are satisfied.")

        # Unclear section
        if report["unclear"]:
            st.markdown('<p class="section-caption">Unclear \u2014 Requires Manual Review</p>', unsafe_allow_html=True)
            for item in report["unclear"]:
                with st.expander(
                    f"{item.get('obligation_id', '?')} \u2014 Unclear"
                ):
                    st.markdown(f"**Reasoning:** {item.get('reasoning', '')}")

        # Satisfied section
        if report["satisfied"]:
            st.markdown('<p class="section-caption">Satisfied Obligations</p>', unsafe_allow_html=True)
            for item in report["satisfied"]:
                st.markdown(
                    f'- **{item.get("obligation_id", "?")}**: '
                    f"{item.get('reasoning', '')[:120]}..."
                )

    # --- Compliance Check History ---
    history = _load_compliance_history()
    if history:
        st.markdown("---")
        st.markdown('<p class="section-caption">Check History</p>', unsafe_allow_html=True)
        st.markdown(
            "Each compliance check run is automatically saved below. "
            "Use this to track how the gap count changes as the BRD is revised."
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
                line=dict(color="#8B3A3A", width=2),
                marker=dict(size=7, color="#8B3A3A"),
                textfont=dict(color="#1A1A1A"),
            ))
            fig_hist.add_trace(go.Scatter(
                x=[r["Version"] for r in hist_rows],
                y=[r["High-Risk"] for r in hist_rows],
                mode="lines+markers",
                name="High-Risk Gaps",
                line=dict(color="#9C7A3C", width=2, dash="dash"),
                marker=dict(size=6, color="#9C7A3C"),
            ))
            fig_hist = _light_plotly_layout(fig_hist, "Gap Count Trend Across BRD Versions")
            fig_hist.update_layout(
                xaxis_title="BRD Version",
                yaxis_title="Count",
                height=300,
                legend=dict(font=dict(color="#6B6560")),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        if st.button("Clear History", type="secondary"):
            with open(COMPLIANCE_HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump([], f)
            st.rerun()


# ---------------------------------------------------------------------------
# View 3: RTM & Dependency Analysis
# ---------------------------------------------------------------------------
elif view == 2:
    st.markdown('<p class="module-label">Module 03</p>', unsafe_allow_html=True)
    st.markdown("## RTM & Dependency Analysis")

    st.markdown(
        "Generate a Requirements Traceability Matrix (RTM) and visualize "
        "the dependency graph between requirements."
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
                    st.success("RTM generated.")
                except Exception as e:
                    st.error(f"RTM generation failed: {e}")

    rtm = st.session_state.rtm_result
    if rtm:
        # Dependency graph
        st.markdown('<p class="section-caption">Dependency Graph</p>', unsafe_allow_html=True)
        from modules.rtm import RTMGenerator as RTM
        edges = rtm.get("dependency_graph", [])
        G = RTM.build_dependency_graph(edges)
        if len(G.nodes) > 0:
            fig = RTM.visualize_graph(G)
            fig = _light_plotly_layout(fig, "Requirement Dependency Graph")
            fig.update_traces(
                marker=dict(size=12, color="#3D2B1F", line=dict(color="#6B6560", width=1)),
                textfont=dict(color="#1A1A1A"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No dependencies identified between requirements.")

        # Impact analysis
        if len(G.nodes) > 0:
            st.markdown('<p class="section-caption">Impact Analysis</p>', unsafe_allow_html=True)
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
                _metric_block(impact["total_impacted"], "Total Impacted Requirements")

        # RTM table
        st.markdown('<p class="section-caption">Requirements Traceability Matrix</p>', unsafe_allow_html=True)
        import pandas as pd
        entries = rtm.get("rtm_entries", [])
        if entries:
            df = pd.DataFrame(entries)
            st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# View 4: Process Gap Analysis
# ---------------------------------------------------------------------------
elif view == 3:
    st.markdown('<p class="module-label">Module 04</p>', unsafe_allow_html=True)
    st.markdown("## Process Gap Analysis")

    st.markdown(
        "Compare As-Is and To-Be processes to identify gaps, bottlenecks, "
        "and improvement opportunities."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-caption">As-Is Process</p>', unsafe_allow_html=True)
        as_is_file = st.file_uploader(
            "Upload As-Is process", type=["txt"], key="as_is_upload",
            label_visibility="collapsed",
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
            label_visibility="collapsed",
        )

    with col2:
        st.markdown('<p class="section-caption">To-Be Process</p>', unsafe_allow_html=True)
        to_be_file = st.file_uploader(
            "Upload To-Be process", type=["txt"], key="to_be_upload",
            label_visibility="collapsed",
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
            label_visibility="collapsed",
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
        st.markdown('<p class="section-caption">Process Metrics</p>', unsafe_allow_html=True)
        metrics = gap_result.get("metrics", {})
        if metrics:
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                _metric_block(metrics.get("as_is_time", "N/A"), "As-Is Time")
            with mc2:
                _metric_block(metrics.get("to_be_time", "N/A"), "To-Be Time")
            with mc3:
                _metric_block(metrics.get("fte_change", "N/A"), "FTE Change")

        # Priority matrix
        fig_pm = create_gap_priority_matrix(gap_result)
        fig_pm = _light_plotly_layout(fig_pm, "Gap Priority Matrix (Impact vs Difficulty)")
        fig_pm.update_traces(
            marker=dict(size=13, color="#3D2B1F", line=dict(color="#6B6560", width=1)),
            textfont=dict(color="#1A1A1A"),
        )
        st.plotly_chart(fig_pm, use_container_width=True)

        # Gaps table
        st.markdown('<p class="section-caption">Identified Gaps</p>', unsafe_allow_html=True)
        import pandas as pd
        gaps = gap_result.get("gaps", [])
        if gaps:
            df = pd.DataFrame(gaps)
            st.dataframe(df, use_container_width=True, hide_index=True)

        # Risks
        risks = gap_result.get("risks", [])
        if risks:
            st.markdown('<p class="section-caption">Transformation Risks</p>', unsafe_allow_html=True)
            for risk in risks:
                st.markdown(f"- {risk}")


# ---------------------------------------------------------------------------
# View 5: Export Report
# ---------------------------------------------------------------------------
elif view == 4:
    st.markdown('<p class="module-label">Module 05</p>', unsafe_allow_html=True)
    st.markdown("## Export Report")

    st.markdown(
        "Export all results to a single Excel file."
    )

    # Check what data is available
    has_data = False
    if st.session_state.extraction_result:
        st.markdown("Requirements extraction results available.")
        has_data = True
    else:
        st.markdown("No requirements extraction results.")

    if st.session_state.compliance_report:
        st.markdown("Compliance gap check results available.")
        has_data = True
    else:
        st.markdown("No compliance gap check results.")

    if st.session_state.rtm_result:
        st.markdown("RTM results available.")
        has_data = True
    else:
        st.markdown("No RTM results.")

    if st.session_state.gap_result:
        st.markdown("Process gap analysis results available.")
        has_data = True
    else:
        st.markdown("No process gap analysis results.")

    st.markdown("---")

    # --- Save demo snapshot ---
    st.markdown('<p class="section-caption">Save Demo Snapshot</p>', unsafe_allow_html=True)
    st.markdown(
        "Save the current session results to `data/demo_results.json`. "
        "This enables offline Demo Mode without API calls \u2014 useful "
        "for interviews or demonstrations where network access is unreliable."
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
        st.success("Report ready for download.")


# ---------------------------------------------------------------------------
# Footer (on every page)
# ---------------------------------------------------------------------------
_render_footer()
