from onssa_ai.corpus.chunker import CorpusChunker
from onssa_ai.schemas.corpus import CorpusDocument, CorpusPage, KnowledgeCorpus


def test_chunker_detects_art_abbreviation_as_article_marker() -> None:
    corpus = KnowledgeCorpus(
        documents=[
            CorpusDocument(
                document_id="decret-2-10-473",
                title="Decret n°2-10-473",
                local_path="decret.pdf",
                metadata={"regulation_type": "decret"},
                pages=[
                    CorpusPage(
                        page_number=3,
                        text=(
                            "TITRE II Des autorisations. "
                            "ART. 7. - Si le dossier n'est pas complet, le service avise le demandeur. "
                            "ART. 8. - Lorsque la demande et le dossier sont conformes, il est "
                            "procede dans un delai maximum de 45 jours a une visite sanitaire."
                        ),
                    )
                ],
            )
        ]
    )

    chunks = CorpusChunker(min_chars=1).build_chunks(corpus)
    article_8 = next(chunk for chunk in chunks if chunk.metadata.article == "ART. 8")

    assert article_8.metadata.chunk_type == "article"
    assert "45 jours" in article_8.text
    assert article_8.metadata.citation_label == "Decret n°2-10-473, ART. 8, p. 3"
