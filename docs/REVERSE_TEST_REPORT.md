# Reverse Test Report — BA Intelligence Toolkit

> **Test run:** 2026-07-01T16:59:21.626370+00:00
> **BRD file:** `data/reverse_test_brd.txt`
> **Model:** deepseek-chat

---

## Purpose

A reverse test verifies that the tool does NOT report false-positive
gaps when given a BRD that deliberately covers all 36 compliance
obligations. If the tool reports gaps against this comprehensive BRD,
those gaps are false positives — the tool is being overly sensitive.

## Results Summary

| Metric | Count |
|--------|-------|
| Total obligations checked | 36 |
| Satisfied | 36 |
| **Gaps (false positives)** | **0** |
| Unclear | 0 |
| Not applicable | 0 |
| High-risk gaps | 0 |

## Token Usage & Cost

| Metric | Value |
|--------|-------|
| API calls | 4 |
| Prompt tokens | 32,288 |
| Completion tokens | 4,014 |
| Total tokens | 36,302 |
| Estimated cost | ¥0.0403 CNY |

## Verdict: PASSED

Zero false-positive gaps were detected. The tool correctly
identified that all 36 obligations are covered by the
comprehensive BRD.

---

## Conclusion

The reverse test **passed**. The tool demonstrated zero false
positives when given a comprehensive BRD covering all 36
obligations. This confirms the tool does not suffer from
over-sensitivity — it does not flag gaps where none exist.
