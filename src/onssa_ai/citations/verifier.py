"""Citation verification placeholder."""

from onssa_ai.schemas.citation import Citation


class CitationVerifier:
    def verify(self, citations: list[Citation]) -> bool:
        return all(citation.chunk_id for citation in citations)
