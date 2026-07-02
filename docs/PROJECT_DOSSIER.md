# BA Intelligence Toolkit — Project Dossier

> A compliance gap reasoning tool for UK banking business analysts.

---

## 1. One-Line Description

This is a compliance gap reasoning tool for UK banking BAs — it doesn't find keywords, it reasons through each KYC/AML obligation to check whether the requirements document covers it, turning the cognitive load of manual checklist review into a traceable, automated judgment.

---

## 2. What Problem Am I Solving?

### 2.1 The Real Pain Point

When a BA receives a requirements document (BRD, meeting transcript), they need to manually check it against regulatory requirements to ensure nothing is missed. This process is:

- **Time-consuming**: manually going through 36 regulatory obligations against a multi-page document
- **Error-prone**: especially for "implicit obligations" — where the requirements document doesn't mention a regulatory term, but the process described has already triggered that obligation
- **Dependent on individual expertise**: a junior BA may not know that a purely digital onboarding flow triggers non-face-to-face risk safeguards under MLR 2017 Reg 33(6)(b)(iii)

### 2.2 Why Existing Tools Aren't Enough

| Tool type | What it does | What it doesn't do |
|-----------|-------------|-------------------|
| GRC platforms (Actimize, LexisNexis) | Enterprise-wide AML transaction monitoring | Don't check BRDs for compliance coverage at the requirements stage |
| Meeting transcription tools (Otter, Fireflies) | Convert speech to text | Don't extract requirements or check compliance |
| Requirements tools (Jira, Confluence) | Track requirements | Don't reason about regulatory coverage |

No tool solves the gap between "requirements document" and "compliance obligation coverage check" — the middle step that BA does manually.

### 2.3 Which Step Does This Tool Solve?

```
[Stakeholder meeting] → [Requirements document] → [THIS TOOL] → [Compliance gap list] → [BA decision & revision]
```

The tool automates the reasoning from requirements document to compliance gap list. Upstream is the BRD; downstream is the BA's decision.

---

## 3. My Design Approach

### 3.1 Core Decision: From Keyword Matching to Compliance Gap Reasoning

| Approach | Question asked | What it requires |
|----------|---------------|-----------------|
| Keyword matching | "What regulatory terms appear in the requirements?" | A keyword list + regex |
| **Gap reasoning (this tool)** | **"What regulatory obligations are implied by these requirements, and are they covered?"** | **A structured obligation checklist + semantic reasoning** |

The latter is what a BA actually does. The former falls apart the moment an interviewer asks: "If the requirements don't mention 'KYC' but implicitly require KYC, can your tool identify it?"

### 3.2 Why an Obligation Checklist, Not a Rule Engine?

The obligation checklist is the process of translating abstract regulatory requirements into operable judgment criteria. The granularity and accuracy of the checklist itself is proof of business judgment. Code is just the executor of the checklist.

### 3.3 Why Narrow to One Scenario?

Rather than superficially covering five regulatory frameworks, this tool goes deep into one scenario: **KYC/AML compliance check for individual retail customer digital account opening**. Being able to thoroughly explain one scenario in an interview is more persuasive than touching five superficially.

### 3.4 The Role Boundary of the LLM

The LLM does not "know" regulatory requirements (that's the checklist's job). It only "judges" whether the requirements document covers a specific obligation on the checklist. This is a semantic reasoning task, not a knowledge retrieval task — which is why we use an LLM, not a rule engine.

---

## 4. The Compliance Obligation Checklist (Core Deliverable)

### 4.1 What Is the Checklist?

A YAML file (`data/compliance_obligations.yaml`) containing 36 structured obligations across 9 categories, covering the full KYC/AML chain for individual retail customer digital account opening. 11 of these are marked `depth: deep` — the obligations most likely to be missed and most illustrative of the gap-reasoning approach.

### 4.2 How Was It Researched?

Read through:
- MLR 2017 (Reg 28/31/33/35/37/40) — full legislation text
- JMLSG Guidance Part I, Chapter 5 — Customer Due Diligence
- FCA FG17-6 — PEP treatment guidance
- FCA Consumer Duty (PRIN 2A)
- UK Digital Identity Trust Framework (DCMS, 2022)

Distilled these into judgment rules. This research process itself is worth describing in the project documentation.

### 4.3 Checklist Field Design

```yaml
- obligation_id: C1
  category: "Enhanced Due Diligence (EDD) Triggers"
  trigger: "When the trigger condition applies to this project"
  obligation: "What must be true / covered"
  how_to_check: "Judgment logic — how to determine if the BRD covers it"
  consequence_if_gap: "What happens if this is a gap"
  severity: high / medium / low
  source: "MLR 2017 Reg 33(6)(b)(iii); JMLSG 5.3.5"
  depth: deep | standard
```

### 4.4 How to Write `how_to_check` (Most Critical)

**Problem**: `how_to_check` is essentially teaching the LLM how to make semantic judgments. The easiest mistake is writing "check whether the BRD mentions XX" — that reverts to keyword thinking.

**Writing rule**: Describe the judgment logic itself, not "what words to look for."

**Wrong** (reverts to keyword thinking):
> how_to_check: Check whether the BRD describes a purely online/non-face-to-face onboarding flow

**Right** (describes judgment logic):
> how_to_check: Determine whether any step in the customer identity verification process described in the BRD involves real-time human interaction between the customer and a firm representative (video call, branch, third-party witness). If all steps involve customer self-submission or automated verification, the non-face-to-face trigger is activated. Once activated, check whether the BRD describes compensating safeguards (biometric liveness detection, multi-source cross-referencing, digital identity service standard).

**Self-check standard (intern test)**: After writing each `how_to_check`, ask: if I don't let the LLM do semantic reasoning, and only allow an intern who doesn't understand compliance to read the BRD following this instruction, can they make the same judgment as me? If "no" (too vague) → rewrite. If "yes" (criteria are clear) → pass.

### 4.5 Representative Obligations for Deep Explanation

These are the `depth: deep` obligations — 11 items that most demonstrate "from keyword matching to gap reasoning." The full list:

| ID | Category | Obligation (summary) |
|----|----------|---------------------|
| A5 | CDD Core | Must not establish business relationship if CDD cannot be completed |
| B1 | Risk Assessment | Must assess ML/TF risk of each customer and apply RBA |
| C1 | EDD Triggers | Non-face-to-face onboarding requires compensating safeguards |
| C2 | EDD Triggers | EDD must include senior management approval + source of funds |
| C4 | EDD Triggers | EDD for unusual/anomalous application patterns at account opening |
| C6 | EDD Triggers | EDD for high-risk jurisdictions — senior management approval |
| D1 | PEP & Sanctions | Sanctions screening at onboarding (real-time, not batch) |
| D2 | PEP & Sanctions | PEP screening including family members and known close associates |
| E1 | Source of Funds | Obtain source of funds information for account opening |
| E2 | Source of Funds | Verify (not just collect) source of wealth for EDD cases |
| F3 | Ongoing Monitoring | Re-screen existing customers when sanctions/PEP lists update |

Four representative examples for deep explanation:

**A5 — CDD completion gate** (MLR 2017 Reg 28(12)):
If CDD cannot be satisfactorily completed, the firm must not establish the business relationship, must not carry out the transaction, or must terminate the relationship. Requirements documents often describe the happy path (successful onboarding) but omit the failure path — what happens when identity verification fails partway through? The tool identifies this gap.

**B1 — Risk-based approach** (MLR 2017 Reg 18):
The firm must assess the ML/TF risk of each customer and apply measures proportionate to that risk. Requirements may describe a single onboarding flow without risk-tiering. Without an explicit risk assessment step, all customers receive the same level of due diligence — violating the risk-based approach.

**C1 — Non-face-to-face risk safeguards** (MLR 2017 Reg 33(6)(b)(iii)):
The most easily missed obligation. Business stakeholders focus on customer experience and may not realize that a purely digital flow triggers additional safeguards. The requirements document may describe using Onfido for "photo ID + selfie" but not specify liveness detection, multi-source verification, or compliance with Reg 28(19) standards. The tool identifies this as a gap even though the word "non-face-to-face" never appears.

**C4 — Application-stage EDD triggers** (MLR 2017 Reg 33(1)(c)):
Requirements documents often cover onboarding risk scoring but omit EDD triggers for unusual or anomalous patterns at the application stage — e.g., multiple applications from the same device, mismatched IP geolocation, or identity documents submitted for multiple applicants. The tool checks whether the BRD describes detection logic for these anomalies and EDD escalation when triggered.

---

## 5. How the Tool Works

### 5.1 Overall Flow

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
[Output: Excel report with all results]
```

### 5.2 The Five Modules

| Module | Input | Output |
|--------|-------|--------|
| 1. Requirements Extraction | Meeting transcript / BRD text | Structured requirements, decisions, actions, risks, assumptions, constraints |
| 2. Compliance Gap Reasoning | Requirements text + obligation checklist | Per-obligation status (satisfied/gap/unclear) with reasoning and consequences |
| 3. RTM & Dependency Analysis | Extracted requirements | Traceability matrix + interactive dependency graph + impact analysis |
| 4. Process Gap Analysis | As-Is and To-Be process descriptions | Gaps, metrics, risks, priority matrix |
| 5. Export | All above results | Excel file with multiple worksheets |

### 5.3 Data Flow for a Complete Run

1. User pastes meeting transcript → Module 1 extracts 10+ structured requirements
2. User clicks "Run Compliance Check" → Module 2 checks each of 36 obligations against the requirements, identifies 5 gaps
3. User clicks "Generate RTM" → Module 3 creates traceability matrix and dependency graph
4. User pastes As-Is/To-Be processes → Module 4 identifies process gaps and priority matrix
5. User clicks "Export" → all results exported to Excel

---

## 6. Demo Scenario

### 6.1 Background

A UK retail bank wants to optimize its digital account opening process, reducing time from 5-7 days to under 5 minutes while maintaining FCA compliance.

### 6.2 Input

A realistic meeting transcript covering 26 discussion points about the digital account opening enhancement project. The transcript mentions KYC, PEPs, sanctions, GDPR, audit trail — it looks comprehensive.

### 6.3 Output

The compliance gap checker identifies **5 real gaps** that the meeting participants (including the compliance officer) did not catch:

| Gap | Obligation | What was missed |
|-----|-----------|-----------------|
| 1 | C1 — Non-face-to-face safeguards | Onfido "photo ID + selfie" mentioned, but no liveness detection, multi-source verification, or Reg 28(19) standard specified |
| 2 | C4 — Application-stage EDD triggers | Risk scoring covers onboarding, but no framework for flagging anomalous application patterns (multiple applications from same device, IP geolocation mismatch) at the application stage |
| 3 | E2 — Source of wealth verification for EDD | PEP screening mentioned, but no SOW verification process for EDD cases |
| 4 | F3 — Ongoing sanctions/PEP rescreening | At-onboarding screening mentioned, but no process for rescreening when lists are updated |
| 5 | A6 — Purpose and nature of relationship | No collection of expected account usage or transaction patterns |

### 6.4 Why These Gaps Matter

These are "the requirements document doesn't mention the keyword, but the obligation is implicitly present and uncovered" — real examples that prove the design works. They represent the kind of omissions that commonly occur when business stakeholders focus on customer experience and even compliance officers in the room don't catch every implicit obligation.

---

## 7. Technical Implementation

### 7.1 Tech Stack and Rationale

| Technology | Why |
|-----------|-----|
| Python | Already skilled; dominant in data/analysis |
| Streamlit | Fast prototyping; interactive demo; no frontend needed |
| DeepSeek API (deepseek-chat) | Semantic reasoning; extremely cost-effective (~¥0.04 per full demo run); fast |
| PyYAML | Checklist as external data file (code-data separation) |
| Plotly | Interactive visualizations (dependency graph, heatmap) |
| NetworkX | Dependency graph construction and impact analysis |
| openpyxl | Excel export (lighter than Word/PDF for MVP) |
| SQLite | Lightweight storage (not used in MVP; session state only) |

### 7.2 Architecture

```
app.py (Streamlit UI)
  ├── ai_engine.py (OpenAI-compatible LLM wrapper + prompt templates + usage tracking)
  ├── modules/
  │   ├── extractor.py (requirements extraction)
  │   ├── compliance.py (compliance gap checker)
  │   ├── rtm.py (RTM + dependency graph + impact analysis)
  │   └── gap_analyzer.py (process gap analysis)
  ├── utils.py (file I/O, Excel export, visualization)
  └── data/
      ├── compliance_obligations.yaml (CORE IP — the checklist)
      ├── sample_transcript.txt (demo input)
      ├── as_is_process.txt (demo As-Is)
      └── to_be_process.txt (demo To-Be)
```

### 7.3 Prompt Engineering Highlights

- **Compliance gap prompt**: explicitly instructs the LLM that "an obligation is NOT satisfied merely because a keyword appears" and "an obligation CAN be a gap even if its keyword never appears"
- **JSON mode**: forces structured output for reliable parsing
- **Batched processing**: obligations sent in batches of 10 to manage prompt length
- **Low temperature (0.3)**: for consistent, deterministic reasoning

### 7.4 Why Code and Checklist Are Decoupled

The checklist is a YAML data file. The code only loads the checklist, calls the LLM, and structures results. To support a different scenario (e.g., corporate client onboarding), replace the YAML — the code stays the same. This is "data-driven design."

---

## 8. Design Decision Record

### 8.1 Why Not Keyword Matching?

**Decision**: Compliance gap reasoning using a structured obligation checklist
**Rejected**: Keyword matching with regex/keyword lists
**Reason**: Keyword matching cannot identify implicit obligations (where the requirement doesn't mention the regulatory term but the obligation is triggered). This is the exact scenario where BAs add value.
**Trade-off**: Gap reasoning requires LLM calls (cost, latency) vs. keyword matching is instant and free. The value of catching implicit gaps justifies the cost.

### 8.2 Why Not Five Regulatory Frameworks?

**Decision**: One scenario (individual retail digital account opening), KYC/AML only
**Rejected**: Five frameworks (KYC/AML, GDPR, FCA Consumer Duty, PSD2, PCI DSS) shallowly
**Reason**: Being able to explain one scenario thoroughly in an interview is more persuasive than touching five superficially. The depth of the obligation checklist is the proof of business judgment.
**Trade-off**: Narrower scope means the tool only applies to one scenario. But the architecture is extensible — adding a new scenario means adding a new YAML file.

### 8.3 Why LLM for Semantic Judgment, Not a Rule Engine?

**Decision**: LLM for compliance gap checking
**Rejected**: Rule engine (deterministic rules coded in Python)
**Reason**: The judgment "does this BRD cover this obligation?" is a semantic reasoning task, not a pattern-matching task. A rule engine would require encoding every possible way an obligation could be satisfied — which is intractable. The LLM reasons about meaning.
**Trade-off**: LLM output is non-deterministic (mitigated by low temperature + JSON mode). A rule engine would be 100% reproducible. But the rule engine cannot do the semantic reasoning that makes this tool valuable.

### 8.4 Why Checklist as YAML, Not Code?

**Decision**: Checklist is a YAML data file
**Rejected**: Hardcode obligations in Python
**Reason**: Separating data from code means the checklist can be iterated independently by someone who understands compliance but doesn't code. Adding/removing/modifying obligations doesn't require code changes. This is "data-driven design."
**Trade-off**: YAML is less expressive than code for complex logic. But the `how_to_check` field captures the judgment logic in natural language, which the LLM interprets.

### 8.5 Why Streamlit, Not Frontend-Backend Separation?

**Decision**: Streamlit for the entire UI
**Rejected**: React/Next.js frontend + FastAPI backend
**Reason**: For a portfolio project, the value is in the compliance reasoning, not the frontend. Streamlit enables rapid prototyping and interactive demo with zero frontend effort. The 2-3 week timeline doesn't allow for learning a frontend framework.
**Trade-off**: Streamlit is less customizable than a real frontend. But for a demo tool, it's sufficient and far more efficient.

---

## 9. Limitations and Future Direction

### 9.1 What the Current Version Cannot Do

- Only covers individual retail customer digital account opening — not corporate clients, investment products, or payments/e-money
- Does not replace human compliance review — it augments it by flagging potential gaps
- Does not integrate with JIRA/Confluence for requirement tracking

### 9.2 False Positive and False Negative Risk

- **False positive** (marks as gap when it shouldn't): mitigated by **reverse testing** — running a deliberately comprehensive BRD that covers all 36 obligations through the tool and verifying zero false-positive gaps are reported. This test has been executed and passed (see `data/reverse_test_brd.txt` and `docs/REVERSE_TEST_REPORT.md`).
- **False negative** (misses a real gap): mitigated by the depth and specificity of the obligation checklist
- Neither can be fully eliminated — the tool is a decision support tool, not an automated compliance decision maker

### 9.3 If Given More Time

- More compliance scenarios (corporate onboarding, e-money, payments)
- Checklist version management (compare old vs new when regulations update)
- JIRA/Confluence integration (export requirements as JIRA tickets)
- More visualizations (Sankey diagram for process flow, Gantt for implementation timeline)
- User feedback loop (BA marks a gap as "accepted risk" or "will address" → tool learns)

### 9.4 Version Tracking (Implemented)

The tool automatically saves every compliance check run to `data/compliance_history.json`, recording:
- Timestamp
- BRD version label (user-inputted, e.g. "v1.0-draft")
- Total obligations checked
- Number satisfied
- Number of gaps
- Number of high-risk gaps

A history table and gap-trend chart are displayed in View 2, allowing the BA to see how the gap count has changed across BRD revisions (e.g. Version 1: 17 gaps → Version 2: 8 gaps). This mirrors a real BA workflow where the BRD goes through multiple review cycles and the compliance position improves with each iteration.

---

## 10. Project File Map

| File | Purpose |
|------|---------|
| `app.py` | Streamlit main application — all UI logic |
| `ai_engine.py` | OpenAI-compatible LLM wrapper + prompt templates + token/cost tracking |
| `modules/extractor.py` | Requirements extraction module |
| `modules/compliance.py` | Compliance gap checker (core module) |
| `modules/rtm.py` | RTM generator + dependency graph + impact analysis |
| `modules/gap_analyzer.py` | Process gap analyzer (As-Is vs To-Be) |
| `utils.py` | File I/O, Excel export, visualization helpers |
| `data/compliance_obligations.yaml` | **Core IP** — the structured obligation checklist |
| `data/sample_transcript.txt` | Demo input — meeting transcript with deliberate gaps |
| `data/as_is_process.txt` | Demo As-Is process |
| `data/to_be_process.txt` | Demo To-Be process |
| `data/demo_results.json` | Pre-computed results for offline demo |
| `data/compliance_history.json` | Version-tracked compliance check history (gap trend across BRD revisions) |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |
| `docs/PROJECT_DOSSIER.md` | This document |
