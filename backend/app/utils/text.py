import re


class TextProcessingUtils:
    """Utilities for preparing project text before embedding."""

    # Regex to keep only word characters and whitespace
    _CLEAN_RE = re.compile(r"[^\w\s]", re.UNICODE)
    _SPACE_RE = re.compile(r"\s+")

    @staticmethod
    def prepare_text(
        title: str,
        relevance: str = "",
        problem: str = "",
        goal: str = "",
        key_tasks: str = "",
        expected_result: str = "",
    ) -> str:
        """Concatenate project fields, lowercase, and strip noise.

        Fields: title + relevance + problem + goal + key_tasks + expected_result.
        """
        parts = [title, relevance, problem, goal, key_tasks, expected_result]
        text = " ".join(p for p in parts if p)
        text = text.lower()
        text = TextProcessingUtils._CLEAN_RE.sub(" ", text)
        text = TextProcessingUtils._SPACE_RE.sub(" ", text).strip()
        return text
