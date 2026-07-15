"""HTML text extraction for ONSSA source pages."""

from pathlib import Path

from bs4 import BeautifulSoup

from onssa_ai.ingestion.models import ExtractedDocument
from onssa_ai.schemas.corpus import CorpusPage


class HtmlExtractor:
    """Extract readable text from downloaded HTML pages."""

    def extract(self, path: Path, fallback_title: str | None = None) -> ExtractedDocument:
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        for element in soup(["script", "style", "noscript", "svg"]):
            element.decompose()

        title = self._title(soup, fallback_title, path)
        text = self._normalize_text(soup.get_text("\n", strip=True))
        return ExtractedDocument(
            title=title,
            document_type="page",
            language=self._detect_language(text),
            pages=[CorpusPage(page_number=1, text=text)] if text else [],
            text=text,
            metadata={"html_title": title},
        )

    def _title(self, soup: BeautifulSoup, fallback_title: str | None, path: Path) -> str:
        if soup.title and soup.title.string and soup.title.string.strip():
            return self._normalize_text(soup.title.string)
        heading = soup.find(["h1", "h2"])
        if heading:
            return self._normalize_text(heading.get_text(" ", strip=True))
        if fallback_title and fallback_title.strip():
            return self._normalize_text(fallback_title)
        return path.stem.replace("_", " ").strip()

    def _detect_language(self, text: str) -> str:
        arabic_chars = sum(1 for char in text[:2000] if "\u0600" <= char <= "\u06ff")
        return "ar" if arabic_chars > 50 else "fr"

    def _normalize_text(self, text: str) -> str:
        return "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())
