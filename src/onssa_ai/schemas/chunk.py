"""Chunk schemas preserving source metadata."""

from pydantic import BaseModel, Field

from onssa_ai.schemas.reference import LegalReference


class ChunkMetadata(BaseModel):
    vertical: str
    domain: str
    subdomain: str
    site_hierarchy: list[str] = Field(default_factory=list)
    site_parent_url: str | None = None
    site_sub_subdomain: str | None = None
    site_sub_subdomain_display: str | None = None
    document_id: str
    document_title: str
    source_url: str | None = None
    local_path: str | None = None
    regulation_type: str | None = None
    language: str = "fr"
    source_file: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    page_numbers: list[int] = Field(default_factory=list)
    article: str | None = None
    article_number: str | None = None
    section: str | None = None
    section_title: str | None = None
    chunk_type: str = "page"
    structure_path: list[str] = Field(default_factory=list)
    document_number: str | None = None
    document_scope: str | None = None
    answer_role: str = "direct_answer"
    outgoing_references: list[LegalReference] = Field(default_factory=list)
    incoming_references: list[LegalReference] = Field(default_factory=list)
    source_hash: str | None = None
    chunk_index: int
    chunk_hash: str
    citation_label: str


class KnowledgeChunk(BaseModel):
    chunk_id: str
    text: str = Field(min_length=1)
    metadata: ChunkMetadata
