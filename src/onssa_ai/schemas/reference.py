"""Legal reference schemas for reference-aware retrieval."""

from pydantic import BaseModel


class LegalReference(BaseModel):
    """A legal or regulatory reference extracted from a chunk."""

    reference_type: str
    document_number: str | None = None
    article_number: str | None = None
    raw_text: str
    resolved_chunk_id: str | None = None
    missing: bool = False

