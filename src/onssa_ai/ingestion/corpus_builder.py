"""Build knowledge_corpus.json from synchronized ONSSA sources."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, Field

from onssa_ai.ingestion.html_extractor import HtmlExtractor
from onssa_ai.ingestion.models import ExtractedDocument, SourceClassification
from onssa_ai.ingestion.pdf_extractor import PdfExtractor
from onssa_ai.ingestion.source_classifier import SourceClassifier
from onssa_ai.ingestion.taxonomy import SiteTaxonomy
from onssa_ai.schemas.corpus import CorpusDocument, KnowledgeCorpus
from onssa_ai.sources.manifest import SourceManifest
from onssa_ai.sources.models import SourceManifestEntry


class CorpusBuildConfig(BaseModel):
    source_manifest_path: Path
    output_path: Path
    report_path: Path
    taxonomy_path: Path = Path("configs/taxonomy.yaml")
    include_pages: bool = False
    include_all_sources: bool = False
    min_text_chars: int = 80
    vertical: str = "regulation"
    domain: str = "reglementation_transversale"
    subdomain: str = "securite_sanitaire"


class CorpusBuildReport(BaseModel):
    generated_at: str
    source_manifest_path: str
    output_path: str
    total_manifest_entries: int = 0
    included_documents: int = 0
    first_slice_documents: int = 0
    unclassified_documents: int = 0
    skipped_documents: int = 0
    failed_documents: int = 0
    failures: list[dict[str, str]] = Field(default_factory=list)


class CorpusBuilder:
    """Build the canonical corpus from local synchronized ONSSA files."""

    def __init__(self, config: CorpusBuildConfig) -> None:
        self.config = config
        self.pdf_extractor = PdfExtractor()
        self.html_extractor = HtmlExtractor()
        self.taxonomy = SiteTaxonomy.from_yaml(config.taxonomy_path)
        self.classifier = SourceClassifier(
            include_all_sources=config.include_all_sources,
            target_vertical=config.vertical,
            target_domain=config.domain,
            target_subdomain=config.subdomain,
            taxonomy=self.taxonomy,
        )

    def build(self) -> CorpusBuildReport:
        manifest = SourceManifest(self.config.source_manifest_path)
        manifest.load()
        generated_at = datetime.now(UTC).isoformat()
        report = CorpusBuildReport(
            generated_at=generated_at,
            source_manifest_path=str(self.config.source_manifest_path),
            output_path=str(self.config.output_path),
            total_manifest_entries=len(manifest.entries),
        )
        documents: list[CorpusDocument] = []

        for entry in manifest.entries.values():
            if not self._can_process(entry):
                report.skipped_documents += 1
                continue

            classification = self.classifier.classify(entry)
            if not classification.include:
                report.skipped_documents += 1
                continue

            try:
                extracted = self._extract(entry)
                if len(extracted.text) < self.config.min_text_chars:
                    report.skipped_documents += 1
                    continue
                documents.append(self._to_corpus_document(entry, extracted, classification))
                report.included_documents += 1
                if (
                    classification.domain == self.config.domain
                    and classification.subdomain == self.config.subdomain
                ):
                    report.first_slice_documents += 1
                else:
                    report.unclassified_documents += 1
            except Exception as exc:  # noqa: BLE001
                report.failed_documents += 1
                report.failures.append({"url": entry.url, "error": str(exc)})

        corpus = KnowledgeCorpus(
            source_name="onssa",
            generated_at=generated_at,
            documents=sorted(documents, key=lambda document: document.document_id),
        )
        self._write_json(self.config.output_path, corpus.model_dump(mode="json"))
        self._write_json(self.config.report_path, report.model_dump(mode="json"))
        return report

    def _can_process(self, entry: SourceManifestEntry) -> bool:
        if entry.status == "failed" or not entry.local_path:
            return False
        if entry.kind not in {"page", "pdf"}:
            return False
        if entry.kind == "page" and not self.config.include_pages:
            return False
        return Path(entry.local_path).exists()

    def _extract(self, entry: SourceManifestEntry) -> ExtractedDocument:
        path = Path(entry.local_path or "")
        if entry.kind == "pdf":
            return self.pdf_extractor.extract(path, fallback_title=entry.title)
        return self.html_extractor.extract(path, fallback_title=entry.title)

    def _to_corpus_document(
        self,
        entry: SourceManifestEntry,
        extracted: ExtractedDocument,
        classification: SourceClassification,
    ) -> CorpusDocument:
        document_id = self._document_id(entry)
        return CorpusDocument(
            document_id=document_id,
            title=extracted.title,
            source_url=entry.url,
            local_path=entry.local_path,
            source_hash=entry.content_sha256,
            document_type=extracted.document_type,
            language=extracted.language,
            vertical=classification.vertical,
            domain=classification.domain,
            subdomain=classification.subdomain,
            pages=extracted.pages,
            text=extracted.text,
            metadata={
                **extracted.metadata,
                "parent_url": entry.parent_url,
                "manifest_status": entry.status,
                "last_seen_at": entry.last_seen_at.isoformat(),
                "classification_reason": classification.reason,
                "classification_confidence": classification.confidence,
                "matched_keywords": classification.matched_keywords,
                "needs_review": classification.needs_review,
                "regulation_type": classification.regulation_type,
                "site_hierarchy": classification.site_hierarchy,
                "site_parent_url": classification.site_parent_url,
                "site_matched_rule": classification.site_matched_rule,
                "site_sub_subdomain": classification.site_sub_subdomain,
                "site_sub_subdomain_display": classification.site_sub_subdomain_display,
            },
        )

    def _document_id(self, entry: SourceManifestEntry) -> str:
        digest_source = f"{entry.url}:{entry.content_sha256 or ''}"
        return f"onssa-{entry.kind}-{sha256(digest_source.encode('utf-8')).hexdigest()[:16]}"

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
