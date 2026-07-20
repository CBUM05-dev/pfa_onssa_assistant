from onssa_ai.citations.builder import CitationBuilder
from onssa_ai.schemas.chunk import ChunkMetadata, KnowledgeChunk
from onssa_ai.schemas.retrieval import RetrievedChunk


def test_citation_quote_is_centered_on_question_terms() -> None:
    chunk = KnowledgeChunk(
        chunk_id="chunk-delay",
        text=(
            "Texte introductif sans la reponse. " * 12
            + "ART. 8. - Lorsque la demande et le dossier l'accompagnant sont conformes "
            "il est procede, par les services vises a l'article 5 ci-dessus, dans un "
            "delai maximum de 45 jours, a une visite sanitaire sur place."
        ),
        metadata=ChunkMetadata(
            vertical="regulation",
            domain="transversal_regulation",
            subdomain="food_safety",
            document_id="doc-delay",
            document_title="Decret test",
            source_file="decret.pdf",
            page_start=3,
            article="ART. 8",
            chunk_index=0,
            chunk_hash="hash",
            citation_label="Decret test, ART. 8, p. 3",
        ),
    )
    citation = CitationBuilder().build(
        [RetrievedChunk(chunk=chunk, score=0.9)],
        question="Quel est le delai maximum pour effectuer la visite sanitaire ?",
    )[0]

    assert citation.quote is not None
    assert "ART. 8" in citation.quote
    assert "45 jours" in citation.quote
    assert not citation.quote.startswith("Texte introductif")
