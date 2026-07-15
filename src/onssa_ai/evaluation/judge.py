"""Deterministic evaluation checks."""


class DeterministicJudge:
    """Rule-based checks for refusal and citation presence."""

    def has_required_citations(self, citation_count: int) -> bool:
        return citation_count > 0
