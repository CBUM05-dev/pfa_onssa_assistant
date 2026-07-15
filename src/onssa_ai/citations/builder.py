"""Citation construction from retrieved evidence."""

from onssa_ai.schemas.citation import Citation
from onssa_ai.schemas.retrieval import RetrievedChunk


class CitationBuilder:
    """Create citation objects from chunk metadata."""

    def build(self, evidence: list[RetrievedChunk]) -> list[Citation]:
        citations: list[Citation] = []
        for item in evidence:
            metadata = item.chunk.metadata
            citations.append(
                Citation(
                    document_id=metadata.document_id,
                    document_title=metadata.document_title,
                    source_file=metadata.source_file,
                    page=metadata.page_start,
                    article=metadata.article,
                    section=metadata.section,
                    chunk_id=item.chunk.chunk_id,
                    quote=item.chunk.text[:300],
                )
            )
        return citations
