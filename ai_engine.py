"""
BA Intelligence Toolkit — AI Engine
OpenAI-compatible LLM wrapper + all prompt templates.
"""

import json
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud: read secrets into os.environ if available *before* importing openai
# so that the OpenAI client picks up LLM_API_KEY/LLM_BASE_URL automatically.
try:
    import streamlit as st
    if hasattr(st, "secrets") and st.secrets:
        for key in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
            try:
                if key not in os.environ:
                    value = st.secrets.get(key)
                    if value:
                        os.environ[key] = str(value)
            except Exception:
                pass
except (ImportError, AttributeError, Exception):
    pass

from openai import OpenAI

# ---------------------------------------------------------------------------
# Pricing — per-token costs in CNY (used for cost estimates in the UI).
# DeepSeek: ~¥1 / 1M input tokens, ~¥2 / 1M output tokens.
# OpenAI prices are converted from USD to CNY at an approximate rate of 7.2.
# ---------------------------------------------------------------------------
MODEL_PRICING_CNY: dict[str, dict[str, float]] = {
    "deepseek-chat": {"input": 1.0e-6, "output": 2.0e-6},
    "deepseek-v4-flash": {"input": 1.0e-6, "output": 2.0e-6},
    "deepseek-reasoner": {"input": 4.0e-6, "output": 16.0e-6},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000 * 7.2, "output": 0.60 / 1_000_000 * 7.2},
    "gpt-4o": {"input": 2.50 / 1_000_000 * 7.2, "output": 10.0 / 1_000_000 * 7.2},
    "gpt-3.5-turbo": {"input": 0.50 / 1_000_000 * 7.2, "output": 1.50 / 1_000_000 * 7.2},
}

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

EXTRACT_REQUIREMENTS_PROMPT = """\
You are an expert Business Analyst specialising in UK banking.
Extract structured requirements from the following meeting transcript or \
document.

For each requirement provide:
- req_id: "REQ-001", "REQ-002", etc.
- title: concise, action-oriented title
- description: detailed description of what the requirement is
- type: one of "Functional", "Non-Functional", "Regulatory"
- priority: "High", "Medium", or "Low"
- source_ref: which discussion point or section this came from

Also extract (as separate lists):
- decisions: key decisions made during the discussion
- actions: action items with owner and deadline if mentioned
- risks: risks identified
- assumptions: assumptions stated
- constraints: constraints mentioned

Transcript / Document:
---
{transcript}
---

Respond ONLY with valid JSON in this exact structure:
{{
  "requirements": [
    {{"req_id": "REQ-001", "title": "...", "description": "...",
      "type": "Functional", "priority": "High", "source_ref": "Point 2"}}
  ],
  "decisions": ["..."],
  "actions": ["..."],
  "risks": ["..."],
  "assumptions": ["..."],
  "constraints": ["..."]
}}
"""

COMPLIANCE_GAP_PROMPT = """\
You are an expert UK banking compliance analyst reviewing a Business \
Requirements Document (BRD) for a digital account-opening project for \
INDIVIDUAL (retail) customers.

You will be given:
1. A structured Compliance Obligation Checklist. Each item is a \
conditional obligation with a trigger, an obligation, and a \
how_to_check field that describes the judgment logic.
2. The BRD / extracted requirements / process description.

Your task: For EACH obligation in the checklist, determine whether the \
BRD COVERS it. Reason about the *meaning* of the requirements, not \
whether certain words appear.

For each obligation output:
- obligation_id
- status: one of ["satisfied", "gap", "unclear", "not_applicable"]
- reasoning: why you reached this status, citing what the BRD says \
(or omits). Be specific about what in the BRD led to your conclusion.
- consequence_if_gap: if status is gap or unclear, what could go wrong \
(regulatory, operational, or reputational). If satisfied, write "N/A".
- suggested_control: if gap, what should be added to the BRD. If \
satisfied, write "N/A".

CRITICAL rules:
- "satisfied" only if the BRD explicitly or implicitly addresses the \
obligation's trigger AND the required measure.
- "gap" if the obligation applies to this project (trigger met) but the \
BRD does not address the measure.
- "unclear" if you cannot tell from the BRD whether the obligation is met.
- "not_applicable" only if the trigger explicitly does not apply (e.g., \
the BRD describes a face-to-face process and the obligation is about \
non-face-to-face risk).
- An obligation is NOT satisfied merely because a related keyword appears. \
Judge by substance.
- An obligation CAN be a gap even if its keyword never appears (e.g., \
the BRD describes a non-face-to-face digital flow but never adds \
safeguards for the non-face-to-face risk).

Compliance Obligation Checklist:
{checklist}

BRD / Requirements / Process:
---
{brd}
---

Respond ONLY with valid JSON:
{{
  "results": [
    {{"obligation_id": "A1", "status": "satisfied",
      "reasoning": "...",
      "consequence_if_gap": "N/A",
      "suggested_control": "N/A"}}
  ]
}}
"""

GAP_ANALYSIS_PROMPT = """\
You are a process improvement expert specialising in banking operations.
Compare the As-Is and To-Be processes and identify gaps.

As-Is Process:
---
{as_is_process}
---

To-Be Process:
---
{to_be_process}
---

For each gap identified, provide:
- gap_id: "GAP-001", "GAP-002", etc.
- description: what the gap is
- gap_type: one of "Bottleneck", "Missing Capability", "Redundant Step", \
"Inefficiency"
- impact: "High", "Medium", or "Low"
- recommendation: what should be done about it

Also provide:
- metrics: process efficiency comparison (time, effort, drop-off rate)
- risks: risks associated with the transformation
- priority_matrix: list of gaps with impact and implementation difficulty \
("High"/"Medium"/"Low" for each)

Respond ONLY with valid JSON:
{{
  "gaps": [
    {{"gap_id": "GAP-001", "description": "...", "gap_type": "...",
      "impact": "High", "recommendation": "..."}}
  ],
  "metrics": {{"as_is_time": "...", "to_be_time": "...", "fte_change": "..."}},
  "risks": ["..."],
  "priority_matrix": [
    {{"gap_id": "GAP-001", "impact": "High", "difficulty": "Medium"}}
  ]
}}
"""

GENERATE_RTM_PROMPT = """\
You are a requirements management expert.
Based on the following extracted requirements, generate a Requirements \
Traceability Matrix (RTM) and a dependency graph.

Requirements:
{requirements}

For each requirement, identify:
- business_need: the business need it addresses
- depends_on: list of req_ids that this requirement depends on (empty \
list if none)
- test_cases: 1-2 suggested test cases
- acceptance_criteria: 1-2 acceptance criteria

Also generate a dependency_graph as a list of edges:
{{"source": "REQ-001", "target": "REQ-003", "type": "depends_on"}}

Respond ONLY with valid JSON:
{{
  "rtm_entries": [
    {{"req_id": "REQ-001", "title": "...", "business_need": "...",
      "depends_on": ["REQ-003"], "test_cases": ["..."],
      "acceptance_criteria": ["..."]}}
  ],
  "dependency_graph": [
    {{"source": "REQ-001", "target": "REQ-003", "type": "depends_on"}}
  ]
}}
"""

# ---------------------------------------------------------------------------
# Client wrapper
# ---------------------------------------------------------------------------

class AIEngine:
    """Thin wrapper around OpenAI-compatible chat completions with JSON mode.

    Supports any provider that implements the OpenAI API spec:
    - OpenAI:  base_url=None (default), model="gpt-4o-mini"
    - DeepSeek: base_url="https://api.deepseek.com", model="deepseek-chat"
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "deepseek-chat",
        base_url: str | None = None,
    ):
        key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "API key not found. Set LLM_API_KEY (or OPENAI_API_KEY) "
                "in .env or pass api_key=..."
            )
        url = base_url or os.getenv("LLM_BASE_URL")
        client_kwargs = {"api_key": key}
        if url:
            client_kwargs["base_url"] = url
        self.client = OpenAI(**client_kwargs)
        self.model = model
        self.usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "calls": 0,
        }

    def generate(self, prompt: str) -> str:
        """Call the model and return the text response."""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that always "
                            "responds with valid JSON when asked to."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        self._record_usage(resp.usage)
        return resp.choices[0].message.content

    def _record_usage(self, usage: Any) -> None:
        """Accumulate token usage from an API response."""
        if usage is None:
            return
        prompt = getattr(usage, "prompt_tokens", 0) or 0
        completion = getattr(usage, "completion_tokens", 0) or 0
        total = getattr(usage, "total_tokens", 0) or 0
        self.usage["prompt_tokens"] += prompt
        self.usage["completion_tokens"] += completion
        # Some providers only report prompt+completion; don't double-count if
        # total is provided separately.
        if total and total != prompt + completion:
            self.usage["total_tokens"] += total
        else:
            self.usage["total_tokens"] += prompt + completion
        self.usage["calls"] += 1

    def get_usage(self) -> dict[str, int]:
        """Return a copy of the accumulated usage counters."""
        return self.usage.copy()

    def reset_usage(self) -> None:
        """Reset accumulated usage counters."""
        self.usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "calls": 0,
        }

    def get_cost_estimate(self, currency: str = "CNY") -> dict[str, float | None]:
        """Estimate cost of the accumulated usage for the current model.

        Returns a dict with keys:
            input_cost, output_cost, total_cost
        Costs are None if no pricing is available for the model.
        """
        pricing = MODEL_PRICING_CNY.get(self.model)
        if pricing is None:
            return {"input_cost": None, "output_cost": None, "total_cost": None}

        input_cost = self.usage["prompt_tokens"] * pricing["input"]
        output_cost = self.usage["completion_tokens"] * pricing["output"]
        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(input_cost + output_cost, 6),
        }

    def generate_json(self, prompt: str, max_retries: int = 2) -> dict:
        """Call the model and return parsed JSON, with fallback for malformed responses."""
        for attempt in range(max_retries + 1):
            text = self.generate(prompt)
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                if attempt < max_retries:
                    # Try to extract JSON from surrounding text
                    import re
                    match = re.search(r'\{[\s\S]*\}', text)
                    if match:
                        try:
                            return json.loads(match.group(0))
                        except json.JSONDecodeError:
                            pass
                    # Retry with a stricter instruction
                    continue
                else:
                    raise ValueError(
                        f"LLM returned invalid JSON after {max_retries + 1} "
                        f"attempts. Last response started with: "
                        f"{text[:200]}..."
                    )
