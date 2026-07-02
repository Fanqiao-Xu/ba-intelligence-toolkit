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
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
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
    st.sidebar.markdown("### Usage & Cost")
    st.sidebar.markdown(f"**Model:** {usage.get('model', 'N/A')}")
    st.sidebar.markdown(
        f"**Calls:** {usage.get('calls', 0)}  \n"
        f"**Tokens:** {usage.get('total_tokens', 0):,} "
        f"({usage.get('prompt_tokens', 0):,} in / "
        f"{usage.get('completion_tokens', 0):,} out)"
    )
    cost = usage.get("cost_cny", {})
    if cost and cost.get("total_cost") is not None:
        st.sidebar.markdown(f"**Est. cost:** ¥{cost['total_cost']:.4f} CNY")
    else:
        st.sidebar.markdown("**Est. cost:** pricing not available")


# ---------------------------------------------------------------------------
# Helper: save / load compliance check history
# ---------------------------------------------------------------------------
def _save_compliance_history(report: dict, version_label: str):
    """Append a compliance check run to the history JSON file.

    Stores: timestamp, version label, summary metrics (total, satisfied,
    gaps, unclear, high_risk_gaps).  This allows tracking how the gap
    count changes across BRD revisions.
    """
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
st.sidebar.title("BA Intelligence Toolkit")
st.sidebar.markdown("---")

st.sidebar.markdown("### Configuration")

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
    "**Scenario:** Individual retail customer, digital (non-face-to-face) "
    "account opening — KYC/AML compliance check"
)

# Render usage / cost metrics in sidebar (live or from demo snapshot)
_render_usage()


# ---------------------------------------------------------------------------
# Main content — view selector
# ---------------------------------------------------------------------------
view = st.radio(
    "Select View",
    options=[
        "1. Input & Requirements Extraction",
        "2. Compliance Gap Reasoning",
        "3. RTM & Dependency Analysis",
        "4. Process Gap Analysis",
        "5. Export Report",
    ],
    horizontal=True,
)

st.markdown("---")


# ---------------------------------------------------------------------------
# View 1: Input & Requirements Extraction
# ---------------------------------------------------------------------------
if view.startswith("1"):
    st.header("1. Input & Requirements Extraction")

    st.markdown(
        "Upload or paste a meeting transcript, BRD draft, or requirements "
        "document. The tool will extract structured requirements, decisions, "
        "actions, risks, assumptions, and constraints."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Input")
        uploaded_file = st.file_uploader(
            "Upload a text file",
            type=["txt", "pdf"],
            help="Upload a .txt or .pdf file containing the transcript or BRD.",
        )

        if uploaded_file:
            st.session_state.input_text = load_uploaded_file(uploaded_file)
            st.success(f"Loaded: {uploaded_file.name}")

        # Load demo transcript button
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
        st.subheader("Extracted Requirements")

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
            st.metric("Requirements", len(reqs))

            # Display requirements in a table
            if reqs:
                import pandas as pd
                df = pd.DataFrame(reqs)
                st.dataframe(
                    df[["req_id", "title", "type", "priority"]],
                    use_container_width=True,
                )

            # Expandable sections for other extracted items
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
elif view.startswith("2"):
    st.header("2. Compliance Gap Reasoning")

    st.markdown(
        "The tool checks the BRD against a structured **Compliance Obligation "
        "Checklist** — not by matching keywords, but by reasoning about "
        "whether each obligation is covered by the requirements."
    )

    st.info(
        "**Checklist scope:** Individual retail customer, digital "
        "(non-face-to-face) account opening — KYC/AML. "
        "Based on MLR 2017, JMLSG Guidance, FCA FG17-6, UK GDPR, "
        "FCA Consumer Duty."
    )

    # Show checklist overview
    if st.session_state.checker:
        with st.expander("View Compliance Obligation Checklist"):
            for o in st.session_state.checker.obligations:
                depth_badge = " 🔴 **[DEEP]**" if o.get("depth") == "deep" else ""
                st.markdown(
                    f"**{o['obligation_id']}** ({o['category']}) "
                    f"— *{o.get('severity', 'medium').upper()}*{depth_badge}"
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
                            pass  # history is best-effort; don't block the check

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

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Obligations", s["total"])
        col2.metric("Satisfied", s["satisfied"], delta_color="off")
        col3.metric("Gaps", s["gaps"], delta_color="inverse")
        col4.metric("High-Risk Gaps", s["high_risk_gaps"], delta_color="inverse")

        st.markdown("---")

        # Heatmap
        st.plotly_chart(
            create_compliance_heatmap(report),
            use_container_width=True,
        )

        # Gaps section (most important)
        st.markdown("### ⚠ Identified Gaps")
        if report["gaps"]:
            for gap in report["gaps"]:
                severity = "high"
                if st.session_state.checker:
                    detail = st.session_state.checker.get_obligation_detail(
                        gap.get("obligation_id", "")
                    )
                    if detail:
                        severity = detail.get("severity", "medium")

                severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                with st.expander(
                    f"{severity_color.get(severity, '⚪')} "
                    f"{gap.get('obligation_id', '?')} — {severity.upper()} risk gap"
                ):
                    st.markdown(f"**Status:** {gap.get('status', '')}")
                    st.markdown(f"**Reasoning:** {gap.get('reasoning', '')}")
                    st.markdown(
                        f"**Consequence if gap:** "
                        f"{gap.get('consequence_if_gap', '')}"
                    )
                    st.markdown(
                        f"**Suggested control:** "
                        f"{gap.get('suggested_control', '')}"
                    )

                    # Show the obligation detail
                    if st.session_state.checker:
                        detail = st.session_state.checker.get_obligation_detail(
                            gap.get("obligation_id", "")
                        )
                        if detail:
                            st.markdown("---")
                            st.markdown(f"**Source:** {detail.get('source', '')}")
                            st.markdown(
                                f"**Obligation:** {detail.get('obligation', '')}"
                            )
        else:
            st.success("No gaps identified! All obligations are satisfied.")

        # Unclear section
        if report["unclear"]:
            st.markdown("### ❓ Unclear (Requires Manual Review)")
            for item in report["unclear"]:
                with st.expander(
                    f"{item.get('obligation_id', '?')} — Unclear"
                ):
                    st.markdown(f"**Reasoning:** {item.get('reasoning', '')}")

        # Satisfied section
        if report["satisfied"]:
            st.markdown("### ✅ Satisfied Obligations")
            for item in report["satisfied"]:
                st.markdown(
                    f"- **{item.get('obligation_id', '?')}**: "
                    f"{item.get('reasoning', '')[:120]}..."
                )

    # --- Compliance Check History ---
    history = _load_compliance_history()
    if history:
        st.markdown("---")
        st.markdown("### 📊 Check History (Gap Trend Across BRD Versions)")
        st.markdown(
            "Each compliance check run is automatically saved below. "
            "Use this to track how the gap count changes as the BRD is "
            "revised."
        )
        import pandas as pd
        hist_rows = []
        for i, h in enumerate(history, 1):
            ts = h.get("timestamp", "")
            # show a human-friendly time (date + HH:MM)
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

        # Simple gap trend chart
        if len(hist_rows) >= 2:
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                x=[r["Version"] for r in hist_rows],
                y=[r["Gaps"] for r in hist_rows],
                mode="lines+markers+text",
                text=[str(r["Gaps"]) for r in hist_rows],
                textposition="top center",
                name="Gaps",
                line=dict(color="#e63946", width=2),
                marker=dict(size=8),
            ))
            fig_hist.add_trace(go.Scatter(
                x=[r["Version"] for r in hist_rows],
                y=[r["High-Risk"] for r in hist_rows],
                mode="lines+markers",
                name="High-Risk Gaps",
                line=dict(color="#f4a261", width=2, dash="dash"),
                marker=dict(size=6),
            ))
            fig_hist.update_layout(
                title="Gap Count Trend Across BRD Versions",
                xaxis_title="BRD Version",
                yaxis_title="Count",
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        # Clear history button
        if st.button("Clear History", type="secondary"):
            with open(COMPLIANCE_HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump([], f)
            st.rerun()


# ---------------------------------------------------------------------------
# View 3: RTM & Dependency Analysis
# ---------------------------------------------------------------------------
elif view.startswith("3"):
    st.header("3. RTM & Dependency Analysis")

    st.markdown(
        "Generate a Requirements Traceability Matrix (RTM) and visualize "
        "the dependency graph between requirements."
    )

    if st.button("Generate RTM", type="primary"):
        if not st.session_state.rtm_gen:
            st.error("Please initialize the AI Engine first (sidebar).")
        elif not st.session_state.extraction_result:
            st.error("Please extract requirements first (View 1).")
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
        st.subheader("Dependency Graph")
        from modules.rtm import RTMGenerator as RTM
        edges = rtm.get("dependency_graph", [])
        G = RTM.build_dependency_graph(edges)
        if len(G.nodes) > 0:
            fig = RTM.visualize_graph(G)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No dependencies identified between requirements.")

        # Impact analysis
        if len(G.nodes) > 0:
            st.subheader("Impact Analysis")
            selected = st.selectbox(
                "Select a requirement to analyze impact:",
                options=list(G.nodes),
            )
            if selected:
                impact = RTM.analyze_impact(G, selected)
                st.markdown(f"**Changed requirement:** {impact['changed']}")
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
        st.subheader("Requirements Traceability Matrix")
        import pandas as pd
        entries = rtm.get("rtm_entries", [])
        if entries:
            df = pd.DataFrame(entries)
            st.dataframe(df, use_container_width=True)


# ---------------------------------------------------------------------------
# View 4: Process Gap Analysis
# ---------------------------------------------------------------------------
elif view.startswith("4"):
    st.header("4. Process Gap Analysis")

    st.markdown(
        "Compare As-Is and To-Be processes to identify gaps, bottlenecks, "
        "and improvement opportunities."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("As-Is Process")
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
        st.subheader("To-Be Process")
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
        st.subheader("Process Metrics")
        metrics = gap_result.get("metrics", {})
        if metrics:
            col1, col2, col3 = st.columns(3)
            col1.metric("As-Is Time", metrics.get("as_is_time", "N/A"))
            col2.metric("To-Be Time", metrics.get("to_be_time", "N/A"))
            col3.metric("FTE Change", metrics.get("fte_change", "N/A"))

        # Priority matrix
        st.plotly_chart(
            create_gap_priority_matrix(gap_result),
            use_container_width=True,
        )

        # Gaps table
        st.subheader("Identified Gaps")
        import pandas as pd
        gaps = gap_result.get("gaps", [])
        if gaps:
            df = pd.DataFrame(gaps)
            st.dataframe(df, use_container_width=True)

        # Risks
        risks = gap_result.get("risks", [])
        if risks:
            st.subheader("Transformation Risks")
            for risk in risks:
                st.markdown(f"- ⚠ {risk}")


# ---------------------------------------------------------------------------
# View 5: Export Report
# ---------------------------------------------------------------------------
elif view.startswith("5"):
    st.header("5. Export Report")

    st.markdown("Export all results to a single Excel file.")

    # Check what data is available
    has_data = False
    if st.session_state.extraction_result:
        st.markdown("✅ Requirements extraction results available")
        has_data = True
    else:
        st.markdown("❌ No requirements extraction results")

    if st.session_state.compliance_report:
        st.markdown("✅ Compliance gap check results available")
        has_data = True
    else:
        st.markdown("❌ No compliance gap check results")

    if st.session_state.rtm_result:
        st.markdown("✅ RTM results available")
        has_data = True
    else:
        st.markdown("❌ No RTM results")

    if st.session_state.gap_result:
        st.markdown("✅ Process gap analysis results available")
        has_data = True
    else:
        st.markdown("❌ No process gap analysis results")

    st.markdown("---")

    # --- Save demo snapshot ---
    st.subheader("Save Demo Snapshot")
    st.markdown(
        "Save the current session results (input, extraction, compliance, "
        "RTM, gap analysis, token usage) to `data/demo_results.json`. "
        "This enables offline Demo Mode without API calls — useful for "
        "interviews or demonstrations where network access is unreliable."
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
