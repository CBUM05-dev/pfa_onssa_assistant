"""HTML text extraction for ONSSA source pages."""

from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from bs4.element import Tag

from onssa_ai.ingestion.models import ExtractedDocument
from onssa_ai.schemas.corpus import CorpusPage


class HtmlExtractor:
    """Extract readable text from downloaded HTML pages."""

    def extract(self, path: Path, fallback_title: str | None = None) -> ExtractedDocument:
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        for element in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
            element.decompose()

        title = self._title(soup, fallback_title, path)
        content_root = self._content_root(soup)
        blocks = self._extract_blocks(content_root, title)
        if not blocks:
            text = self._normalize_text(content_root.get_text("\n", strip=True))
            blocks = [
                {
                    "block_type": "html_section",
                    "title": title,
                    "heading_path": [title],
                    "text": text,
                }
            ] if text else []
        text = "\n\n".join(str(block["text"]) for block in blocks if str(block.get("text", "")))
        return ExtractedDocument(
            title=title,
            document_type="page",
            language=self._detect_language(text),
            pages=[
                CorpusPage(page_number=index, text=str(block["text"]))
                for index, block in enumerate(blocks, start=1)
                if str(block.get("text", "")).strip()
            ],
            text=text,
            metadata={"html_title": title, "html_blocks": blocks},
        )

    def _content_root(self, soup: BeautifulSoup) -> Tag:
        for selector in [
            "main",
            "article",
            ".entry-content",
            ".elementor",
            ".elementor-location-single",
            ".site-main",
            "body",
        ]:
            candidate = soup.select_one(selector)
            if isinstance(candidate, Tag):
                return candidate
        return soup

    def _extract_blocks(self, root: Tag, title: str) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        heading_path = [title]
        text_lines: list[str] = []

        def flush_text() -> None:
            text = self._normalize_text("\n".join(text_lines))
            text_lines.clear()
            if not text:
                return
            blocks.append(
                {
                    "block_type": "html_section",
                    "title": heading_path[-1] if heading_path else title,
                    "heading_path": list(heading_path),
                    "text": self._block_text(heading_path, text),
                }
            )

        for element in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "table", "img"]):
            if not isinstance(element, Tag):
                continue
            if element.find_parent(["table"]):
                continue
            name = element.name.lower()
            if name in {"h1", "h2", "h3", "h4"}:
                flush_text()
                heading_text = self._normalize_text(element.get_text(" ", strip=True))
                if heading_text:
                    level = int(name[1])
                    base_length = max(0, level - 1)
                    heading_path = [*heading_path[:base_length], heading_text]
                continue
            if name == "table":
                flush_text()
                table_text = self._table_to_text(element)
                if table_text:
                    table_index = 1 + sum(
                        1 for block in blocks if block.get("block_type") == "html_table"
                    )
                    blocks.append(
                        {
                            "block_type": "html_table",
                            "title": heading_path[-1] if heading_path else title,
                            "heading_path": list(heading_path),
                            "table_index": table_index,
                            "text": self._block_text(heading_path, table_text),
                        }
                    )
                continue
            if name == "img":
                image_text = self._image_text(element)
                if image_text:
                    flush_text()
                    blocks.append(
                        {
                            "block_type": "html_image",
                            "title": heading_path[-1] if heading_path else title,
                            "heading_path": list(heading_path),
                            "image_src": element.get("src"),
                            "text": self._block_text(heading_path, image_text),
                        }
                    )
                continue
            paragraph = self._normalize_text(element.get_text(" ", strip=True))
            if paragraph:
                text_lines.append(paragraph)

        flush_text()
        return self._deduplicate_blocks(blocks)

    def _table_to_text(self, table: Tag) -> str:
        rows = self._table_rows(table)
        if not rows:
            return ""
        markdown = self._table_to_markdown(rows)
        prose = self._table_to_prose(rows)
        if prose:
            return f"{markdown}\n\nTexte du tableau:\n{prose}"
        return markdown

    def _table_rows(self, table: Tag) -> list[list[str]]:
        rows: list[list[str]] = []
        for row in table.find_all("tr"):
            if not isinstance(row, Tag):
                continue
            cells = [
                self._normalize_text(cell.get_text(" ", strip=True))
                for cell in row.find_all(["th", "td"])
                if isinstance(cell, Tag)
            ]
            if any(cells):
                rows.append(cells)
        return rows

    def _table_to_markdown(self, rows: list[list[str]]) -> str:
        if not rows:
            return ""
        width = max(len(row) for row in rows)
        normalized_rows = [row + [""] * (width - len(row)) for row in rows]
        header = normalized_rows[0]
        separator = ["---"] * width
        body = normalized_rows[1:]
        markdown_rows = [self._markdown_row(header), self._markdown_row(separator)]
        markdown_rows.extend(self._markdown_row(row) for row in body)
        return "\n".join(markdown_rows)

    def _table_to_prose(self, rows: list[list[str]]) -> str:
        if len(rows) < 2:
            return ""
        width = max(len(row) for row in rows)
        normalized_rows = [row + [""] * (width - len(row)) for row in rows]
        headers = [
            header if header else f"Colonne {index + 1}"
            for index, header in enumerate(normalized_rows[0])
        ]
        lines: list[str] = []
        for row in normalized_rows[1:]:
            if not any(cell.strip() for cell in row):
                continue
            subject = row[0].strip()
            details = [
                f"{headers[index]} {cell.strip()}"
                for index, cell in enumerate(row[1:], start=1)
                if cell.strip()
            ]
            if subject and details:
                lines.append(f"- {subject}: {'; '.join(details)}.")
            elif subject:
                lines.append(f"- {headers[0]} {subject}.")
            elif details:
                lines.append(f"- {'; '.join(details)}.")
        return "\n".join(lines)

    def _markdown_row(self, row: list[str]) -> str:
        return "| " + " | ".join(cell.replace("|", "/") for cell in row) + " |"

    def _image_text(self, image: Tag) -> str:
        values = [
            str(image.get(attribute, "")).strip()
            for attribute in ["alt", "title", "aria-label"]
        ]
        text = self._normalize_text(" ".join(value for value in values if value))
        if not text:
            return ""
        return f"Image: {text}"

    def _block_text(self, heading_path: list[str], text: str) -> str:
        headings = [heading for heading in heading_path if heading]
        if not headings:
            return text
        return f"{' > '.join(headings)}\n{text}"

    def _deduplicate_blocks(self, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduplicated: list[dict[str, Any]] = []
        seen: set[str] = set()
        for block in blocks:
            text = str(block.get("text", "")).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            deduplicated.append(block)
        return deduplicated

    def _title(self, soup: BeautifulSoup, fallback_title: str | None, path: Path) -> str:
        heading = soup.find(["h1", "h2"])
        if heading:
            return self._normalize_text(heading.get_text(" ", strip=True))
        if soup.title and soup.title.string and soup.title.string.strip():
            return self._normalize_text(soup.title.string)
        if fallback_title and fallback_title.strip():
            return self._normalize_text(fallback_title)
        return path.stem.replace("_", " ").strip()

    def _detect_language(self, text: str) -> str:
        arabic_chars = sum(1 for char in text[:2000] if "\u0600" <= char <= "\u06ff")
        return "ar" if arabic_chars > 50 else "fr"

    def _normalize_text(self, text: str) -> str:
        return "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())
