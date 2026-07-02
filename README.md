# BA Intelligence Toolkit

A compliance gap reasoning tool for UK banking business analysts.

**Live Demo:** _link will be added after deployment_

## What It Does

This tool checks a Business Requirements Document (BRD) against a structured **Compliance Obligation Checklist** — not by matching keywords, but by reasoning about whether each obligation is covered by the requirements.

**Scenario:** Individual retail customer, digital (non-face-to-face) account opening — KYC/AML compliance check.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and add your DeepSeek (or OpenAI) API key

# 3. Run the app
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Demo Mode

To explore the tool without an API key:
1. Check "Load Demo Data" in the sidebar
2. Click "Load Demo Results"
3. Navigate through the views to see pre-computed results

## How It Works

```
[Input: meeting transcript / BRD]
        ↓
[Module 1: Requirements Extraction]
        ↓
[Module 2: Compliance Gap Reasoning] ← [Compliance Obligation Checklist (YAML)]
        ↓
[Module 3: RTM Generation & Dependency Graph]
        ↓
[Module 4: Process Gap Analysis (As-Is vs To-Be)]
        ↓
[Output: Excel report]
```

## Key Design Decision

The compliance module does NOT match keywords. It reasons through each obligation:

- **Keyword matching** asks: "What regulatory terms appear in the requirements?"
- **Gap reasoning** asks: "What regulatory obligations are implied by these requirements, and are they covered?"

This means the tool can identify a gap even when the requirements document never mentions the regulatory term — because it reasons about the *meaning* of the requirements, not the words.

## Version Tracking

Every compliance check run is automatically saved with a BRD version label, timestamp, and summary metrics (total / satisfied / gaps / high-risk gaps). View 2 displays a history table and gap-trend chart so you can see how the gap count changes across BRD revisions (e.g. v1: 17 gaps → v2: 8 gaps).

## Compliance Obligation Checklist

The checklist (`data/compliance_obligations.yaml`) contains 36 structured obligations across 9 categories covering:

- **A.** Customer Identification & Verification (CDD Core)
- **B.** Risk Assessment & Risk-Based Approach
- **C.** Enhanced Due Diligence (EDD) Triggers
- **D.** PEP & Sanctions Screening
- **E.** Source of Funds & Source of Wealth
- **F.** Ongoing Monitoring
- **G.** Record Keeping
- **H.** Data Protection (GDPR)
- **I.** FCA Consumer Duty

Sources: MLR 2017, JMLSG Guidance, FCA FG17-6, UK GDPR, FCA Consumer Duty.

## Tech Stack

- **Python** + **Streamlit** (UI)
- **OpenAI-compatible API** (DeepSeek `deepseek-chat` or OpenAI `gpt-4o-mini`, semantic reasoning)
- **PyYAML** (checklist as external data)
- **Plotly** + **NetworkX** (visualizations)
- **openpyxl** (Excel export)

## Project Documentation

See `docs/PROJECT_DOSSIER.md` for the complete project dossier, including design decisions, limitations, and future directions.

## Project Structure

```
ba-intelligence-toolkit/
├── app.py                      # Streamlit main entry (5 views)
├── ai_engine.py                # OpenAI-compatible LLM wrapper + prompt templates
├── utils.py                    # Shared helpers
├── requirements.txt
├── .env.example                # API key template
├── .streamlit/
│   └── config.toml             # Streamlit server config
├── data/
│   ├── compliance_obligations.yaml   # 36 obligations, 9 categories, 11 deep
│   ├── sample_transcript.txt         # Demo meeting transcript (5 intentional gaps)
│   ├── reverse_test_brd.txt          # Reverse-test BRD (covers all 36 obligations)
│   ├── demo_results.json             # Pre-computed results for offline demo
│   ├── as_is_process.txt             # As-Is process description
│   └── to_be_process.txt             # To-Be process description
├── modules/
│   ├── extractor.py             # Module 1: Requirements extraction
│   ├── compliance.py            # Module 2: Compliance gap reasoning
│   ├── rtm.py                   # Module 3: RTM + dependency graph
│   └── gap_analyzer.py          # Module 4: As-Is vs To-Be gap analysis
└── docs/
    ├── PROJECT_DOSSIER.md       # Full project dossier
    └── ADVERSARIAL_REVIEW.md    # Adversarial review (35 questions + tech debt)
```

## Deploy Your Own

This app is deployed on [Streamlit Community Cloud](https://streamlit.io/cloud) (free).

1. Fork this repository to your GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository, set main file path to `app.py`
5. In "Secrets", add your API key:
   ```toml
   LLM_API_KEY = "your-deepseek-api-key"
   LLM_BASE_URL = "https://api.deepseek.com"
   LLM_MODEL = "deepseek-chat"
   ```
6. Click Deploy

## License

MIT — see [LICENSE](LICENSE) file.

## Author

**Fanqiao (Faye) Xu** — MSc International Economics, Banking and Finance (Distinction), Cardiff University.

