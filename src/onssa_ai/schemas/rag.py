"""RAG service schemas."""

from typing import Literal

from pydantic import BaseModel, Field

from onssa_ai.schemas.citation import Citation
from onssa_ai.schemas.retrieval import RetrievedChunk, RetrievalFilters


class RagRequest(BaseModel):
    question: str = Field(min_length=1)
    vertical: str = "regulation"
    domain: str = "reglementation_transversale"
    subdomain: str = "securite_sanitaire"
    language: str = "fr"
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)


class RagResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    evidence: list[RetrievedChunk] = Field(default_factory=list)
    confidence: Literal["sufficient", "insufficient"]
    refused: bool
    request_id: str
