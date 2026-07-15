"""Citation formatting helpers."""

from onssa_ai.schemas.citation import Citation


def format_citation(citation: Citation) -> str:
    parts = [citation.document_title]
    if citation.article:
        parts.append(f"article {citation.article}")
    if citation.page:
        parts.append(f"p. {citation.page}")
    return ", ".join(parts)
