"""Schemas for the generated ONSSA knowledge corpus."""

from typing import Any

from pydantic import BaseModel, Field


class CorpusPage(BaseModel):
    page_number: int
    text: str


class CorpusDocument(BaseModel):
    document_id: str
    title: str
    source_url: str | None = None
    local_path: str | None = None
    source_hash: str | None = None
    document_type: str = "pdf"
    language: str = "fr"
    vertical: str = "regulation"
    domain: str = "transversal_regulation"
    subdomain: str = "food_safety"
    pages: list[CorpusPage] = Field(default_factory=list)
    text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeCorpus(BaseModel):
    schema_version: str = "1.0"
    source_name: str = "onssa"
    generated_at: str | None = None
    documents: list[CorpusDocument]
