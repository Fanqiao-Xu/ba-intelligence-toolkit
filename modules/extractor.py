"""
BA Intelligence Toolkit — Requirements Extractor
Extracts structured requirements from meeting transcripts / BRD text.
"""

from ai_engine import AIEngine, EXTRACT_REQUIREMENTS_PROMPT


class RequirementsExtractor:
    """Extract structured requirements from unstructured text."""

    def __init__(self, engine: AIEngine):
        self.engine = engine

    def extract(self, text: str) -> dict:
        """Extract requirements, decisions, actions, risks, etc.

        Args:
            text: meeting transcript or BRD document text.

        Returns:
            dict with keys: requirements, decisions, actions, risks,
            assumptions, constraints.
        """
        prompt = EXTRACT_REQUIREMENTS_PROMPT.format(transcript=text)
        result = self.engine.generate_json(prompt)
        # Ensure all keys exist
        for key in ("requirements", "decisions", "actions", "risks",
                     "assumptions", "constraints"):
            if key not in result:
                result[key] = []
        return result
