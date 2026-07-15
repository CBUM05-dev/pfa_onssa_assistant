"""Evaluation schemas."""

from pydantic import BaseModel, Field


class GoldenQuestion(BaseModel):
    question: str
    expected_document_ids: list[str] = Field(default_factory=list)
    must_refuse: bool = False
    notes: str | None = None
