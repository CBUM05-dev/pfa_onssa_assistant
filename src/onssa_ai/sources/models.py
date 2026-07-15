"""Source synchronization models."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


SourceKind = Literal["page", "pdf"]
SourceStatus = Literal["new", "changed", "unchanged", "failed"]


class DiscoveredSource(BaseModel):
    url: str
    kind: SourceKind
    depth: int
    parent_url: str | None = None


class SourceManifestEntry(BaseModel):
    url: str
    kind: SourceKind
    local_path: str | None = None
    content_sha256: str | None = None
    status: SourceStatus
    title: str | None = None
    parent_url: str | None = None
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: str | None = None


class SyncSummary(BaseModel):
    source_name: str
    discovered_pages: int = 0
    discovered_pdfs: int = 0
    downloaded_new: int = 0
    downloaded_changed: int = 0
    unchanged: int = 0
    failed: int = 0
