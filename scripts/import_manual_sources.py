"""Import manually saved ONSSA HTML pages into the source manifest."""

import argparse
import json
import shutil
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from onssa_ai.sources.downloader import SourceDownloader
from onssa_ai.sources.manifest import SourceManifest
from onssa_ai.sources.models import SourceManifestEntry


class ManualPage(BaseModel):
    url: str
    local_file: Path
    parent_url: str | None = None


class ManualSourcesConfig(BaseModel):
    manifest_path: Path
    pages_dir: Path
    pages: list[ManualPage] = Field(default_factory=list)


class ImportReport(BaseModel):
    generated_at: str
    config_path: str
    manifest_path: str
    imported: int = 0
    unchanged: int = 0
    failed: int = 0
    failures: list[dict[str, str]] = Field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import manually saved source pages.")
    parser.add_argument(
        "--config",
        default="configs/manual_institutionnel_pages.yaml",
        help="Manual source import YAML configuration.",
    )
    parser.add_argument(
        "--report-path",
        default="data/sources/manual_import_report.json",
        help="Import report JSON path.",
    )
    return parser.parse_args()


def load_config(path: Path) -> ManualSourcesConfig:
    with path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = yaml.safe_load(file) or {}
    return ManualSourcesConfig.model_validate(data.get("manual_sources", {}))


def write_report(path: Path, report: ImportReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(report.model_dump(mode="json"), file, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)
    manifest = SourceManifest(config.manifest_path)
    manifest.load()
    downloader = SourceDownloader(timeout_seconds=30, user_agent="manual-import")
    report = ImportReport(
        generated_at=datetime.now(UTC).isoformat(),
        config_path=str(config_path),
        manifest_path=str(config.manifest_path),
    )

    for page in config.pages:
        try:
            content = page.local_file.read_bytes()
            downloader._raise_for_blocked_source(page.url, content, "text/html")
            content_hash = sha256(content).hexdigest()
            old_hash = manifest.get_hash(page.url)
            target_path = config.pages_dir / downloader._filename_for_url(page.url, "html")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if old_hash == content_hash and target_path.exists():
                status = "unchanged"
                report.unchanged += 1
            else:
                status = "changed" if old_hash else "new"
                shutil.copyfile(page.local_file, target_path)
                report.imported += 1
            title = downloader._extract_title(content, "text/html")
            manifest.upsert(
                SourceManifestEntry(
                    url=page.url,
                    kind="page",
                    local_path=str(target_path),
                    content_sha256=content_hash,
                    status=status,
                    title=title,
                    parent_url=page.parent_url,
                )
            )
        except Exception as exc:  # noqa: BLE001
            report.failed += 1
            report.failures.append({"url": page.url, "error": str(exc)})
            manifest.upsert(
                SourceManifestEntry(
                    url=page.url,
                    kind="page",
                    status="failed",
                    parent_url=page.parent_url,
                    error=str(exc),
                )
            )

    manifest.save()
    write_report(Path(args.report_path), report)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
