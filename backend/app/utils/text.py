import re


class TextProcessingUtils:
    """Utilities for preparing project text before embedding."""

    # Regex to keep only word characters and whitespace
    _CLEAN_RE = re.compile(r"[^\w\s]", re.UNICODE)
    _SPACE_RE = re.compile(r"\s+")

    @staticmethod
    def prepare_text(
        title: str,
        problem: str | None = None,
        goal: str | None = None,
        expected_result: str | None = None,
    ) -> str:
        """Concatenate project fields, lowercase, and strip noise.

        Fields: title + problem + goal + expected_result joined with a space.
        """
        parts = [title or "", problem or "", goal or "", expected_result or ""]
        text = " ".join(p for p in parts if p)
        text = text.lower()
        text = TextProcessingUtils._CLEAN_RE.sub(" ", text)
        text = TextProcessingUtils._SPACE_RE.sub(" ", text).strip()
        return text
