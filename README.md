# BA Intelligence Toolkit

A compliance gap analysis tool for UK digital bank account onboarding.

Built by **Fanqiao (Faye) Xu** — MSc International Economics, Banking and Finance (Cardiff University, Distinction, 2025). Currently based in London, seeking Business Analyst roles in financial services and FinTech.

## What it does

The tool checks a Business Requirements Document (BRD) against a structured 36-obligation compliance checklist covering KYC/AML requirements for individual retail customer digital onboarding in the UK. It identifies compliance gaps using semantic reasoning — not keyword matching.

For each gap, the tool provides:
- The specific obligation that is not covered
- The reasoning behind the gap identification
- The regulatory consequence if the gap is not addressed
- A suggested control to remediate the gap
- The legal source (MLR 2017, JMLSG Guidance, FCA FG17-6, UK GDPR, FCA Consumer Duty)

## Why I built it

BRDs written by business teams rarely cover all KYC/AML obligations systematically. Compliance gaps are typically discovered late — during audit or regulatory review — when the cost of remediation is high. This tool shifts the compliance check left to the requirements stage, allowing BAs to self-review before submission.

## Core design decisions

**Semantic reasoning over keyword matching.** The compliance obligation checklist defines judgment logic for each obligation — not a list of keywords to search for. A BRD describing a fully digital onboarding flow triggers the non-face-to-face high-risk obligation even if those words never appear in the document.

**Checklist as intellectual property.** The 36-obligation checklist is the core asset of the tool. It was built from primary sources: MLR 2017 (Reg 28, 33, 35, 40), JMLSG Part I Chapter 5, FCA FG17-6, UK GDPR, and FCA Consumer Duty (PRIN 2A). The code loads this checklist and uses an LLM to reason against it — changing the scenario requires only replacing the checklist file.

**Explicit scope boundaries.** Each obligation includes a defined trigger condition. Obligations that apply only post-onboarding (e.g. ongoing transaction monitoring) are explicitly excluded from scope, preventing false positives for requirements that onboarding BRDs legitimately do not cover.

## Modules

1. Requirements Extraction — extracts structured requirements, decisions, actions, risks, assumptions, and constraints from meeting transcripts or BRD drafts
2. Compliance Gap Reasoning — checks extracted requirements against the 36-obligation checklist
3. RTM & Dependency Analysis — generates a Requirements Traceability Matrix and maps dependencies between requirements
4. Process Gap Analysis — compares As-Is and To-Be process descriptions and identifies gaps
5. Export Report — exports a full summary to Excel

## Regulatory scope

Scenario: Individual retail customer, non-face-to-face (digital channel) account opening — KYC/AML compliance check.

Applicable regimes: MLR 2017, FCA AML regime (SYSC 6.3), FCA Consumer Duty (PRIN 2A), UK GDPR / Data Protection Act 2018.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your DeepSeek (or OpenAI-compatible) API key to .env
streamlit run app.py
```

## Live demo

https://ba-intelligence-toolkit-app.streamlit.app
