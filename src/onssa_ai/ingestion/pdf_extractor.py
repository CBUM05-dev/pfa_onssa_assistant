"""PDF text extraction for ONSSA source documents."""

from pathlib import Path

from onssa_ai.ingestion.models import ExtractedDocument
from onssa_ai.schemas.corpus import CorpusPage


class PdfExtractor:
    """Extract text page by page from PDF files."""

    def extract(self, path: Path, fallback_title: str | None = None) -> ExtractedDocument:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Missing dependency: install pypdf to build the corpus.") from exc

        reader = PdfReader(str(path))
        pages: list[CorpusPage] = []
        for index, page in enumerate(reader.pages, start=1):
            text = self._normalize_text(page.extract_text() or "")
            if text:
                pages.append(CorpusPage(page_number=index, text=text))

        title = self._extract_title(reader.metadata, fallback_title, path)
        full_text = "\n\n".join(page.text for page in pages)
        return ExtractedDocument(
            title=title,
            document_type="pdf",
            language=self._detect_language(path.name, full_text),
            pages=pages,
            text=full_text,
            metadata={
                "page_count": len(reader.pages),
                "extracted_page_count": len(pages),
                "pdf_metadata": {
                    key.strip("/"): str(value)
                    for key, value in (reader.metadata or {}).items()
                    if value is not None
                },
            },
        )

    def _extract_title(
        self,
        metadata: object,
        fallback_title: str | None,
        path: Path,
    ) -> str:
        title = getattr(metadata, "title", None)
        if title and str(title).strip():
            return self._normalize_text(str(title))
        if fallback_title and fallback_title.strip():
            return self._normalize_text(fallback_title)
        return path.stem.replace("_", " ").replace("-", " ").strip()

    def _detect_language(self, filename: str, text: str) -> str:
        lowered = filename.lower()
        if "_ar" in lowered or "lang=ar" in lowered:
            return "ar"
        if "_en" in lowered or "lang=en" in lowered:
            return "en"
        arabic_chars = sum(1 for char in text[:2000] if "\u0600" <= char <= "\u06ff")
        if arabic_chars > 50:
            return "ar"
        return "fr"

    def _normalize_text(self, text: str) -> str:
        lines = [" ".join(line.split()) for line in text.splitlines()]
        return "\n".join(line for line in lines if line).strip()
