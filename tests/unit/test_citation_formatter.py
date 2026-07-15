from onssa_ai.citations.formatter import format_citation
from onssa_ai.schemas.citation import Citation


def test_format_citation_includes_article_and_page() -> None:
    citation = Citation(
        document_id="doc-1",
        document_title="Reglement test",
        page=2,
        article="4",
        chunk_id="chunk-1",
    )
    assert format_citation(citation) == "Reglement test, article 4, p. 2"
