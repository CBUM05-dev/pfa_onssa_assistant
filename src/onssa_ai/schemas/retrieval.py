"""Retrieval request and result schemas."""

from pydantic import BaseModel, Field

from onssa_ai.schemas.chunk import KnowledgeChunk


class RetrievalFilters(BaseModel):
    vertical: str | None = None
    domain: str | None = None
    subdomain: str | None = None
    site_sub_subdomain: str | None = None
    document_id: str | None = None
    language: str | None = None


class RetrievedChunk(BaseModel):
    chunk: KnowledgeChunk
    score: float
    rerank_score: float | None = None


class RetrievalRequest(BaseModel):
    question: str = Field(min_length=1)
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    top_k: int | None = None
