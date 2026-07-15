"""Ingestion models."""

from pydantic import BaseModel, Field

from onssa_ai.schemas.corpus import CorpusPage


class ExtractedDocument(BaseModel):
    title: str
    document_type: str
    language: str
    pages: list[CorpusPage] = Field(default_factory=list)
    text: str
    metadata: dict[str, object] = Field(default_factory=dict)


class SourceClassification(BaseModel):
    include: bool
    vertical: str = "regulation"
    domain: str = "unclassified"
    subdomain: str = "unclassified"
    language: str = "fr"
    regulation_type: str | None = None
    confidence: str = "low"
    matched_keywords: list[str] = Field(default_factory=list)
    needs_review: bool = True
    site_hierarchy: list[str] = Field(default_factory=list)
    site_parent_url: str | None = None
    site_matched_rule: str | None = None
    site_sub_subdomain: str | None = None
    site_sub_subdomain_display: str | None = None
    reason: str
