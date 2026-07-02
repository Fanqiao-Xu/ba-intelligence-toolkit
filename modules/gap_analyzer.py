"""
BA Intelligence Toolkit — Process Gap Analyzer
Compares As-Is and To-Be processes and identifies gaps.
"""

from ai_engine import AIEngine, GAP_ANALYSIS_PROMPT


class GapAnalyzer:
    """Analyze gaps between As-Is and To-Be processes."""

    def __init__(self, engine: AIEngine):
        self.engine = engine

    def analyze(self, as_is_process: str, to_be_process: str) -> dict:
        """Compare As-Is and To-Be processes.

        Args:
            as_is_process: text describing the current process.
            to_be_process: text describing the target process.

        Returns:
            dict with keys: gaps, metrics, risks, priority_matrix
        """
        prompt = GAP_ANALYSIS_PROMPT.format(
            as_is_process=as_is_process,
            to_be_process=to_be_process,
        )
        result = self.engine.generate_json(prompt)

        # Ensure all keys exist
        for key in ("gaps", "metrics", "risks", "priority_matrix"):
            if key not in result:
                result[key] = [] if key != "metrics" else {}

        return result
