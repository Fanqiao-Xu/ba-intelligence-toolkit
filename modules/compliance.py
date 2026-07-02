"""
BA Intelligence Toolkit — Compliance Gap Checker
Checks a BRD against a structured compliance obligation checklist.

Design principle: the checklist is an EXTERNAL data file (YAML), not
hardcoded keywords. The code only loads the checklist, calls the LLM to
reason about each obligation, and structures the result. To support a
different scenario, replace the YAML — the code stays the same.
"""

import json
from pathlib import Path

import yaml
from ai_engine import AIEngine, COMPLIANCE_GAP_PROMPT


class ComplianceGapChecker:
    """Check a BRD against a compliance obligation checklist."""

    def __init__(self, engine: AIEngine, checklist_path: str | Path):
        self.engine = engine
        self.checklist_path = Path(checklist_path)
        self.obligations = self._load_obligations()

    def _load_obligations(self) -> list[dict]:
        """Load the YAML checklist and return the obligations list."""
        with open(self.checklist_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("obligations", [])

    def check(self, brd_text: str) -> dict:
        """Run the compliance gap check against the BRD.

        Obligations are sent in batches (by category) to keep each LLM
        call focused and within token limits.

        Returns a report dict with:
            total, satisfied, gaps, unclear, not_applicable,
            high_risk_gaps, raw_results
        """
        all_results = []
        expected_ids = {o["obligation_id"] for o in self.obligations}

        # Group obligations into batches of ~10 for manageable prompt size
        batch_size = 10
        for i in range(0, len(self.obligations), batch_size):
            batch = self.obligations[i : i + batch_size]
            batch_ids = {o["obligation_id"] for o in batch}
            checklist_json = json.dumps(batch, ensure_ascii=False, indent=2)
            prompt = COMPLIANCE_GAP_PROMPT.format(
                checklist=checklist_json,
                brd=brd_text,
            )
            resp = self.engine.generate_json(prompt)
            batch_results = resp.get("results", [])
            all_results.extend(batch_results)

            # Validate: every obligation in this batch should have a result
            returned_ids = {r.get("obligation_id") for r in batch_results}
            missing = batch_ids - returned_ids
            if missing:
                # Fill in missing obligations as "unclear" rather than silently dropping
                for mid in missing:
                    all_results.append({
                        "obligation_id": mid,
                        "status": "unclear",
                        "reasoning": "LLM did not return a result for this "
                                     "obligation. Manual review required.",
                        "consequence_if_gap": "Unknown — requires manual review.",
                        "suggested_control": "Re-run the check or review manually.",
                    })

        return self._build_report(all_results)

    def _build_report(self, results: list[dict]) -> dict:
        """Structure raw results into a summary report."""
        satisfied = [r for r in results if r.get("status") == "satisfied"]
        gaps = [r for r in results if r.get("status") == "gap"]
        unclear = [r for r in results if r.get("status") == "unclear"]
        not_applicable = [
            r for r in results if r.get("status") == "not_applicable"
        ]

        # Map obligation IDs to severity for high-risk gap identification
        severity_map = {
            o["obligation_id"]: o.get("severity", "medium")
            for o in self.obligations
        }
        high_risk_gaps = [
            r for r in gaps
            if severity_map.get(r.get("obligation_id"), "medium") == "high"
        ]

        return {
            "total": len(results),
            "satisfied": satisfied,
            "gaps": gaps,
            "unclear": unclear,
            "not_applicable": not_applicable,
            "high_risk_gaps": high_risk_gaps,
            "raw_results": results,
            "summary": {
                "total": len(results),
                "satisfied": len(satisfied),
                "gaps": len(gaps),
                "unclear": len(unclear),
                "not_applicable": len(not_applicable),
                "high_risk_gaps": len(high_risk_gaps),
            },
        }

    def get_obligation_detail(self, obligation_id: str) -> dict | None:
        """Look up the full detail of an obligation by ID."""
        for o in self.obligations:
            if o["obligation_id"] == obligation_id:
                return o
        return None
