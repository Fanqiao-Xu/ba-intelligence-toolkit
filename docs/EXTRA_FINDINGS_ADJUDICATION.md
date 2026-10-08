# Extra Findings Adjudication — BA Intelligence Toolkit

> **Adjudication date:** 2026-10-08
> **Source run:** `data/demo_results.json` (demo snapshot)
> **Test document:** `data/sample_transcript.txt`
> **Model:** deepseek-chat

---

## Purpose

The forward test (demo transcript with 5 deliberately planted gaps) reported
**18 gaps in total**: 4 of the 5 designed gaps were caught (C4, E2, F3, A6;
C1 was missed), plus **14 findings that were not part of the designed ground
truth**.

By strict scoring, anything outside the predefined answer key is *unverified*
— calling these 14 findings "true gaps" without checking would be false
precision. This document records the manual adjudication of each extra
finding: whether the document genuinely fails to cover the obligation, and
whether the model's reasoning holds.

## Method

Each gap finding's reasoning cites specific locations in the test document
(what it says, and what it does not say). A gap is a **claim of absence** —
for a ~120-line test document, verifiable by reading the document against
each reasoning chain.

## Results: 13 verified true, 1 contestable

| # | ID | Obligation | Verdict | Evidence (transcript item) |
|---|----|-----------|---------|---------------------------|
| 1 | A2 | Collect & verify residential address | **True gap** | Item 4 mentions Experian for risk scoring only; no address verification requirement anywhere |
| 2 | A5 | No account if CDD cannot be completed | **True gap** | Only a branch fallback (item 23); no failure branch stating the account will not be opened |
| 3 | B2 | Risk factors incomplete | **True gap** | Item 7 lists exactly three factors (screening result, credit score, ID confidence); no geographical risk etc. |
| 4 | C2 | PEP-specific EDD measures | **True gap** | Screening only (item 3); no senior management approval, SoW verification, or enhanced monitoring |
| 5 | C5 | Handling of false/stolen ID documents | **True gap** | Not mentioned anywhere |
| 6 | C6 | Manual review content undefined | **True gap** | Item 5 routes high-risk to compliance; what the review entails is not described |
| 7 | E1 | Source-of-funds collection | **True gap** | Not mentioned anywhere |
| 8 | E3 | SOF/SOW evidence requirements | **True gap** | Not mentioned anywhere |
| 9 | F1 | Ongoing transaction monitoring | **Contestable** | Item 21 explicitly delegates to the existing transaction monitoring system and declares it out of project scope. Whether delegation to an existing system counts as coverage is a judgment call; the model judged strictly. Recorded as *arguable*, not *true* |
| 10 | F2 | Periodic risk-rating review | **True gap** | Risk scoring is performed once, at onboarding (item 7); no refresh or event-triggered reassessment |
| 11 | F4 | SAR escalation path | **True gap** | No MLRO/NCA reporting path anywhere |
| 12 | H4 | Data subject rights (DSAR, erasure) | **True gap** | Not mentioned anywhere |
| 13 | I1 | Fair value assessment | **True gap** | Consumer Duty is raised only for accessibility (item 8); no fair value assessment of fees/charges |
| 14 | I3 | Rejection/communication transparency | **True gap** | Item 24 logs rejection reasons internally; no requirements on customer-facing communication |

### Unclear findings (2)

| ID | Obligation | Assessment |
|----|-----------|------------|
| D3 | Screening hit escalation process | Correctly cautious — document routes hits to manual review but does not describe the escalation/decision process |
| G2 | Transaction record retention | Correctly cautious — reasoning explicitly notes transaction records "may be handled by the core banking system, but the BRD does not confirm" — no forced conclusion |

Both are appropriate `absence-of-evidence` judgments rather than forced
binary verdicts.

## Interpretation

**The two tests measure different things:**

- **Reverse test = precision instrument.** A fully-compliant document yields
  0 false positives. It answers: *does the tool report when it should not?*
- **Forward test = recall instrument.** Designed gaps yield 4/5 caught. It
  answers: *does the tool miss what it should report?*

The 14 extra findings fall **between the two instruments** — they could only
be resolved by manual adjudication, recorded here.

**Why 14 extra findings is not surprising:** the test input is a meeting
transcript, not a complete BRD. It deliberately describes only a slice of the
onboarding flow, so most obligations are genuinely uncovered *for this
document*. The tool's report about what this document fails to cover is
accurate; a production BRD would cover more; triage remains a human task.

## Conclusion

13 of 14 extra findings are verified true gaps. 1 (F1, ongoing monitoring) is
recorded as **contestable** — a defensible strict reading, but a judgment
call the user should resolve with the document author rather than accept
blindly. This adjudication discipline — refusing to label unverified findings
as "true", and scoring one of the tool's own outputs as arguable — is the
same epistemic standard the tool applies to the documents it reviews.
