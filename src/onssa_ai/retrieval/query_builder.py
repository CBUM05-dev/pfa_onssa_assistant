"""Query preparation placeholder."""


class QueryBuilder:
    """Normalize user questions before retrieval."""

    def build(self, question: str) -> str:
        return " ".join(question.split())
