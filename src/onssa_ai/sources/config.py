"""Source synchronization configuration."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, HttpUrl


class SourceConfig(BaseModel):
    name: str
    base_url: HttpUrl
    seed_urls: list[HttpUrl]
    allowed_domains: list[str]
    max_depth: int = Field(default=2, ge=0, le=5)
    include_url_patterns: list[str] = Field(default_factory=list)
    exclude_url_patterns: list[str] = Field(default_factory=list)
    pages_dir: Path
    pdfs_dir: Path
    images_dir: Path = Path("data/raw/images")
    manifest_path: Path
    preserve_url_paths: bool = False
    verify_ssl: bool = True
    request_timeout_seconds: int = Field(default=30, ge=1)
    user_agent: str = "ONSSA-AI-Service-SourceSync/0.1"


class SourcesConfig(BaseModel):
    sources: list[SourceConfig]


def load_sources_config(path: Path) -> SourcesConfig:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return SourcesConfig.model_validate(data)
