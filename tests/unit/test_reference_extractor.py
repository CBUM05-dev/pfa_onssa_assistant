from onssa_ai.references.reference_extractor import (
    enrich_chunks_with_references,
    extract_references,
)
from onssa_ai.schemas.chunk import ChunkMetadata, KnowledgeChunk


def test_extract_decret_article_reference() -> None:
    refs = extract_references("conformément au décret n°2-10-473 article 43")

    assert refs[0].reference_type == "decret"
    assert refs[0].document_number == "2-10-473"
    assert refs[0].article_number == "43"


def test_extract_reference_when_article_precedes_document() -> None:
    refs = extract_references("en application de l'article 43 du décret n°2-10-473")

    assert refs[0].reference_type == "decret"
    assert refs[0].document_number == "2-10-473"
    assert refs[0].article_number == "43"


def test_enrich_resolves_outgoing_reference_to_article_chunk() -> None:
    source = _chunk(
        "source",
        "Arrêté n°2470-15 conformément au décret n°2-10-473 article 43.",
        "Arrêté n°2470-15",
        None,
        "arrete",
    )
    target = _chunk(
        "target",
        "Article 43. Les guides sont élaborés par les organisations professionnelles.",
        "Décret n°2-10-473",
        "Article 43",
        "decret",
    )

    enriched = enrich_chunks_with_references([source, target])

    assert enriched[0].metadata.outgoing_references[0].resolved_chunk_id == "target"
    assert enriched[0].metadata.outgoing_references[0].missing is False
    assert enriched[1].metadata.incoming_references


def _chunk(
    chunk_id: str,
    text: str,
    title: str,
    article: str | None,
    regulation_type: str,
) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk_id,
        text=text,
        metadata=ChunkMetadata(
            vertical="regulation",
            domain="transversal_regulation",
            subdomain="food_safety",
            document_id=chunk_id,
            document_title=title,
            regulation_type=regulation_type,
            article=article,
            chunk_index=0,
            chunk_hash=f"hash-{chunk_id}",
            citation_label=title,
        ),
    )
