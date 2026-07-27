"""Source synchronization orchestration."""

from onssa_ai.sources.config import SourceConfig
from onssa_ai.sources.crawler import SourceCrawler
from onssa_ai.sources.downloader import SourceDownloader
from onssa_ai.sources.manifest import SourceManifest
from onssa_ai.sources.models import SourceManifestEntry, SyncSummary


class SourceSyncService:
    """Synchronize configured source pages and PDFs to local storage."""

    def __init__(self, config: SourceConfig) -> None:
        self.config = config
        self.crawler = SourceCrawler(config)
        self.downloader = SourceDownloader(
            timeout_seconds=config.request_timeout_seconds,
            user_agent=config.user_agent,
            verify_ssl=config.verify_ssl,
        )
        self.manifest = SourceManifest(config.manifest_path)

    def sync(self) -> SyncSummary:
        self.manifest.load()
        summary = SyncSummary(source_name=self.config.name)
        discovered = self.crawler.discover()

        for source in discovered:
            if source.kind == "page":
                summary.discovered_pages += 1
                target_dir = self.config.pages_dir
                suffix = "html"
            elif source.kind == "pdf":
                summary.discovered_pdfs += 1
                target_dir = self.config.pdfs_dir
                suffix = "pdf"
            else:
                summary.discovered_images += 1
                target_dir = self.config.images_dir
                suffix = self._image_suffix(source.url)

            try:
                content = self.downloader.download(source.url)
                old_hash = self.manifest.get_hash(source.url)
                if old_hash is None:
                    status = "new"
                    summary.downloaded_new += 1
                elif old_hash != content.content_sha256:
                    status = "changed"
                    summary.downloaded_changed += 1
                else:
                    status = "unchanged"
                    summary.unchanged += 1

                local_path = self.downloader.write(
                    content,
                    target_dir,
                    suffix,
                    preserve_url_path=self.config.preserve_url_paths,
                )
                self.manifest.upsert(
                    SourceManifestEntry(
                        url=source.url,
                        kind=source.kind,
                        local_path=str(local_path),
                        content_sha256=content.content_sha256,
                        status=status,
                        title=content.title,
                        parent_url=source.parent_url,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                summary.failed += 1
                self.manifest.upsert(
                    SourceManifestEntry(
                        url=source.url,
                        kind=source.kind,
                        status="failed",
                        parent_url=source.parent_url,
                        error=str(exc),
                    )
                )

        self.manifest.save()
        return summary

    def _image_suffix(self, url: str) -> str:
        lowered = url.lower().split("?", maxsplit=1)[0]
        for suffix in ["png", "jpg", "jpeg", "webp", "gif"]:
            if lowered.endswith(f".{suffix}"):
                return suffix
        return "img"
