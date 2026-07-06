# BA Intelligence Toolkit

> A compliance gap analysis tool for UK digital bank account onboarding — built to shift compliance checks left to the requirements stage.

Built by **Fanqiao (Faye) Xu** — MSc International Economics, Banking and Finance (Cardiff University, Distinction, 2025). Currently based in London, seeking Business Analyst roles in financial services and FinTech.

🔗 **Live Demo:** [ba-intelligence-toolkit-app.streamlit.app](https://ba-intelligence-toolkit-app.streamlit.app)

---

## What it does

The tool checks a Business Requirements Document (BRD) against a structured **36-obligation compliance checklist** covering KYC/AML requirements for individual retail customer digital onboarding in the UK. It identifies compliance gaps using **semantic reasoning** — not keyword matching.

For each gap, the tool provides:
- The specific obligation that is not covered
- The reasoning behind the gap identification
- The regulatory consequence if the gap is not addressed
- A suggested control to remediate the gap
- The legal source (MLR 2017, JMLSG Guidance, FCA FG17-6, UK GDPR, FCA Consumer Duty)

## Why I built it

BRDs written by business teams rarely cover all KYC/AML obligations systematically. Compliance gaps are typically discovered late — during audit or regulatory review — when the cost of remediation is high. This tool shifts the compliance check **left** to the requirements stage, allowing BAs to self-review before submission.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                     │
│         (app.py — 5 modules, tabbed interface)           │
├──────┬──────┬──────┬──────┬──────────────────────────────┤
│ Ext- │ Comp │ RTM & │ Proc │  Export                     │
│ ract │ lian │ Deps  │ ess  │  (Excel)                    │
│ ion  │ ce   │      │ Gaps │                              │
├──────┴──────┴──────┴──────┴──────────────────────────────┤
│                    AI Engine (ai_engine.py)               │
│        DeepSeek LLM via OpenAI-compatible API             │
│      Semantic reasoning against obligation checklist      │
├───────────────────────────────────────────────────────────┤
│                    Modules (modules/)                      │
│  ┌───────────┐ ┌─────────────┐ ┌────────────────────┐    │
│  │ extractor │ │ compliance  │ │   gap_analyzer     │    │
│  │    .py    │ │    .py      │ │      .py           │    │
│  └───────────┘ └─────────────┘ └────────────────────┘    │
│  ┌──────────────────────────────────────────────────┐    │
│  │                   rtm.py                          │    │
│  └──────────────────────────────────────────────────┘    │
├───────────────────────────────────────────────────────────┤
│                    Data Layer (data/)                      │
│  ┌────────────────────────┐  ┌─────────────────────────┐  │
│  │ compliance_obligations │  │ sample_transcript.txt   │  │
│  │       .yaml (55KB)     │  │ reverse_test_brd.txt   │  │
│  │  36 obligations,       │  │ as_is/to_be_process    │  │
│  │  5 regulatory regimes  │  │ demo_results.json      │  │
│  └────────────────────────┘  └─────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

## Core design decisions

**1. Semantic reasoning over keyword matching.**
The compliance obligation checklist defines judgment logic for each obligation — not a list of keywords to search for. A BRD describing a fully digital onboarding flow triggers the non-face-to-face high-risk obligation even if those words never appear in the document.

**2. Checklist as intellectual property.**
The 36-obligation checklist (`compliance_obligations.yaml`, 55KB) is the core asset of the tool. It was built from primary sources: MLR 2017 (Reg 28, 33, 35, 40), JMLSG Part I Chapter 5, FCA FG17-6, UK GDPR, and FCA Consumer Duty (PRIN 2A). The code loads this checklist and uses an LLM to reason against it — changing the scenario requires only replacing the checklist file.

**3. Explicit scope boundaries.**
Each obligation includes a defined trigger condition. Obligations that apply only post-onboarding (e.g. ongoing transaction monitoring) are explicitly excluded from scope, preventing false positives for requirements that onboarding BRDs legitimately do not cover.

## Modules

| # | Module | What it does |
|---|--------|-------------|
| 1 | **Requirements Extraction** | Extracts structured requirements, decisions, actions, risks, assumptions, and constraints from meeting transcripts or BRD drafts |
| 2 | **Compliance Gap Reasoning** | Checks extracted requirements against the 36-obligation checklist using LLM semantic reasoning |
| 3 | **RTM & Dependency Analysis** | Generates a Requirements Traceability Matrix and maps dependencies between requirements |
| 4 | **Process Gap Analysis** | Compares As-Is and To-Be process descriptions and identifies gaps |
| 5 | **Export Report** | Exports a full summary to Excel |

## Regulatory scope

**Scenario:** Individual retail customer, non-face-to-face (digital channel) account opening — KYC/AML compliance check.

**Applicable regimes:**
- MLR 2017 (Reg 28, 33, 35, 40)
- FCA AML regime (SYSC 6.3)
- FCA Consumer Duty (PRIN 2A)
- UK GDPR / Data Protection Act 2018
- JMLSG Guidance Part I

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| AI Engine | DeepSeek (OpenAI-compatible API) |
| Data | PyYAML, Pandas, PyPDF2 |
| Visualization | Plotly, NetworkX |
| Export | openpyxl (Excel) |
| Deployment | Streamlit Community Cloud |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your DeepSeek (or OpenAI-compatible) API key to .env
streamlit run app.py
```

## Project Structure

```
ba-intelligence-toolkit/
├── app.py                    # Streamlit frontend (62KB, 5 tabbed modules)
├── ai_engine.py              # LLM reasoning engine (12KB)
├── utils.py                  # Shared utilities
├── run_demo_snapshot.py      # Demo runner — generates snapshot results
├── run_reverse_test.py       # Reverse test — validates against known BRD
├── requirements.txt
├── .env.example
├── .streamlit/
├── modules/
│   ├── extractor.py          # Requirements extraction module
│   ├── compliance.py         # Compliance gap reasoning module
│   ├── gap_analyzer.py       # Process gap analysis module
│   └── rtm.py                # RTM & dependency analysis module
├── data/
│   ├── compliance_obligations.yaml  # 36-obligation checklist (55KB, core IP)
│   ├── sample_transcript.txt        # Demo input
│   ├── reverse_test_brd.txt         # Validation BRD
│   ├── as_is_process.txt            # As-Is process for gap analysis
│   ├── to_be_process.txt            # To-Be process for gap analysis
│   ├── demo_results.json            # Cached demo output
│   └── compliance_history.json      # Historical scan results
└── docs/
```

## License

MIT License — see [LICENSE](LICENSE)
