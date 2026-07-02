#!/usr/bin/env python3
"""
Demo Snapshot Generator — BA Intelligence Toolkit
=================================================
Runs the full pipeline (extraction + compliance + RTM + gap analysis)
against the sample transcript and As-Is/To-Be processes, then saves
the results to data/demo_results.json for offline Demo Mode.

Usage:
    cd ba-intelligence-toolkit
    python run_demo_snapshot.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from ai_engine import AIEngine
from modules.extractor import RequirementsExtractor
from modules.compliance import ComplianceGapChecker
from modules.rtm import RTMGenerator
from modules.gap_analyzer import GapAnalyzer

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHECKLIST_PATH = DATA_DIR / "compliance_obligations.yaml"
TRANSCRIPT_PATH = DATA_DIR / "sample_transcript.txt"
AS_IS_PATH = DATA_DIR / "as_is_process.txt"
TO_BE_PATH = DATA_DIR / "to_be_process.txt"
DEMO_RESULTS_PATH = DATA_DIR / "demo_results.json"


def main():
    print("=" * 70)
    print("DEMO SNAPSHOT GENERATOR — BA Intelligence Toolkit")
    print("=" * 70)
    print()

    # Load inputs
    transcript = (DATA_DIR / "sample_transcript.txt").read_text(encoding="utf-8")
    as_is = (DATA_DIR / "as_is_process.txt").read_text(encoding="utf-8")
    to_be = (DATA_DIR / "to_be_process.txt").read_text(encoding="utf-8")

    print(f"Transcript: {len(transcript)} chars")
    print(f"As-Is:      {len(as_is)} chars")
    print(f"To-Be:      {len(to_be)} chars")
    print()

    # Initialize engine
    print("Initializing DeepSeek engine...")
    engine = AIEngine(model="deepseek-chat", base_url="https://api.deepseek.com")
    print(f"  Model: {engine.model}")
    print()

    # Step 1: Extract requirements
    print("[1/4] Extracting requirements...")
    extractor = RequirementsExtractor(engine)
    extraction_result = extractor.extract(transcript)
    reqs = extraction_result.get("requirements", [])
    print(f"  Extracted {len(reqs)} requirements")
    print()

    # Step 2: Compliance gap check
    print("[2/4] Running compliance gap check...")
    checker = ComplianceGapChecker(engine, CHECKLIST_PATH)
    compliance_report = checker.check(transcript)
    s = compliance_report["summary"]
    print(f"  Total: {s['total']}, Satisfied: {s['satisfied']}, "
          f"Gaps: {s['gaps']}, Unclear: {s['unclear']}")
    print()

    # Step 3: RTM
    print("[3/4] Generating RTM...")
    rtm_gen = RTMGenerator(engine)
    rtm_result = rtm_gen.generate(reqs)
    entries = rtm_result.get("rtm_entries", [])
    edges = rtm_result.get("dependency_graph", [])
    print(f"  RTM entries: {len(entries)}, Dependency edges: {len(edges)}")
    print()

    # Step 4: Process gap analysis
    print("[4/4] Analyzing process gaps...")
    gap_analyzer = GapAnalyzer(engine)
    gap_result = gap_analyzer.analyze(as_is, to_be)
    gaps = gap_result.get("gaps", [])
    print(f"  Process gaps identified: {len(gaps)}")
    print()

    # Token usage
    usage = engine.get_usage()
    cost = engine.get_cost_estimate("CNY")
    print("-" * 70)
    print("TOKEN USAGE & COST")
    print("-" * 70)
    print(f"  API calls:        {usage['calls']}")
    print(f"  Prompt tokens:    {usage['prompt_tokens']:,}")
    print(f"  Completion tokens: {usage['completion_tokens']:,}")
    print(f"  Total tokens:     {usage['total_tokens']:,}")
    if cost.get("total_cost") is not None:
        print(f"  Estimated cost:   ¥{cost['total_cost']:.4f} CNY")
    print()

    # Save snapshot
    snapshot = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "input_text": transcript,
        "extraction_result": extraction_result,
        "compliance_report": compliance_report,
        "rtm_result": rtm_result,
        "gap_result": gap_result,
        "as_is_text": as_is,
        "to_be_text": to_be,
        "usage": {
            "model": engine.model,
            **usage,
            "cost_cny": cost,
        },
    }

    with open(DEMO_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"Demo snapshot saved to: {DEMO_RESULTS_PATH}")
    print()
    print("=" * 70)
    print("DONE — Demo Mode is now fully functional with pre-computed results.")
    print("=" * 70)


if __name__ == "__main__":
    main()
