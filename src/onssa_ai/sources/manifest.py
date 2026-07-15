"""Manifest persistence for source synchronization."""

import json
from pathlib import Path

from onssa_ai.sources.models import SourceManifestEntry


class SourceManifest:
    """Track source URL state across synchronization runs."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: dict[str, SourceManifestEntry] = {}

    def load(self) -> None:
        if not self.path.exists():
            self.entries = {}
            return
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        self.entries = {
            url: SourceManifestEntry.model_validate(entry)
            for url, entry in data.get("entries", {}).items()
        }

    def get_hash(self, url: str) -> str | None:
        entry = self.entries.get(url)
        return entry.content_sha256 if entry else None

    def upsert(self, entry: SourceManifestEntry) -> None:
        self.entries[entry.url] = entry

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "entries": {
                url: entry.model_dump(mode="json")
                for url, entry in sorted(self.entries.items())
            }
        }
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
