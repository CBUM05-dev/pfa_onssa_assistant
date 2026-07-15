"""Citation schemas for regulatory traceability."""

from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    document_title: str
    source_file: str | None = None
    page: int | None = None
    article: str | None = None
    section: str | None = None
    chunk_id: str
    quote: str | None = Field(default=None, description="Short evidence excerpt.")
