"""Structure-aware chunk generation for ONSSA regulatory documents."""

import re
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Literal

from onssa_ai.schemas.chunk import ChunkMetadata, KnowledgeChunk
from onssa_ai.schemas.corpus import CorpusDocument, CorpusPage, KnowledgeCorpus
from onssa_ai.references.reference_extractor import enrich_chunks_with_references


ChunkStrategy = Literal["structure_aware", "page", "character"]


@dataclass
class RegulatoryUnit:
    text: str
    page_numbers: list[int]
    chunk_type: str
    title: str | None = None
    article: str | None = None
    section: str | None = None
    structure_path: list[str] = field(default_factory=list)


class CorpusChunker:
    """Create citation-safe chunks from corpus pages.

    The default strategy is structure-aware:
    - detect legal/regulatory boundaries such as Article, Chapitre, Section, Titre, Annexe;
    - preserve those units when they fit;
    - split only oversized units with overlap;
    - fall back to page-level units when no structure exists.
    """

    MARKER_RE = re.compile(
        r"(?P<prefix>^|(?<=[.;:])\s+)"
        r"(?P<marker>"
        r"(?:Article|ARTICLE)\s+(?:premier|PREMIER|[0-9]+|[IVXLCDM]+)"
        r"|(?:Art|ART)\.?\s*(?:[0-9]+|[IVXLCDM]+)"
        r"|(?:Chapitre|CHAPITRE|Section|SECTION|Titre|TITRE|Annexe|ANNEXE)"
        r"(?:\s+(?:premier|PREMIER|[0-9]+|[IVXLCDM]+))?"
        r")"
        r"(?=\s|[.:;-])"
    )

    def __init__(
        self,
        max_chars: int = 1800,
        overlap_chars: int = 220,
        min_chars: int = 120,
        strategy: ChunkStrategy = "structure_aware",
        prefer_structure_boundaries: bool = True,
    ) -> None:
        if overlap_chars >= max_chars:
            msg = "overlap_chars must be smaller than max_chars"
            raise ValueError(msg)
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars
        self.min_chars = min_chars
        self.strategy = strategy
        self.prefer_structure_boundaries = prefer_structure_boundaries

    def build_chunks(self, corpus: KnowledgeCorpus) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []
        for document in corpus.documents:
            units = self._document_units(document)
            for unit in units:
                for split_unit in self._split_unit_if_needed(unit):
                    if len(split_unit.text) < self.min_chars:
                        continue
                    chunk_index = len(chunks)
                    chunks.append(self._build_chunk(document, split_unit, chunk_index))
        return enrich_chunks_with_references(chunks)

    def _document_units(self, document: CorpusDocument) -> list[RegulatoryUnit]:
        if document.document_type == "page":
            html_units = self._html_units(document)
            if html_units:
                return html_units
        if self.strategy == "character":
            return [
                RegulatoryUnit(
                    text=document.text or "",
                    page_numbers=[page.page_number for page in document.pages],
                    chunk_type="document",
                )
            ]
        if self.strategy == "page" or not self.prefer_structure_boundaries:
            return [self._page_unit(page) for page in document.pages]

        units = self._structure_units(document.pages)
        return units if units else [self._page_unit(page) for page in document.pages]

    def _html_units(self, document: CorpusDocument) -> list[RegulatoryUnit]:
        blocks = document.metadata.get("html_blocks")
        if not isinstance(blocks, list):
            return []
        units: list[RegulatoryUnit] = []
        for index, block in enumerate(blocks, start=1):
            if not isinstance(block, dict):
                continue
            text = self._normalize_text(str(block.get("text") or ""))
            if len(text) < self.min_chars:
                continue
            block_type = str(block.get("block_type") or "html_section")
            title = str(block.get("title") or "").strip() or None
            heading_path_value = block.get("heading_path") or []
            heading_path = [
                str(value).strip()
                for value in heading_path_value
                if str(value).strip()
            ] if isinstance(heading_path_value, list) else []
            units.append(
                RegulatoryUnit(
                    text=text,
                    page_numbers=[index],
                    chunk_type=block_type,
                    title=title,
                    section=title,
                    structure_path=heading_path,
                )
            )
        return units

    def _structure_units(self, pages: list[CorpusPage]) -> list[RegulatoryUnit]:
        units: list[RegulatoryUnit] = []
        current: RegulatoryUnit | None = None
        current_path: list[str] = []

        for page in pages:
            segments = self._segments_for_page(page.text)
            if not segments:
                if current:
                    current.text = self._join_text(current.text, page.text)
                    if page.page_number not in current.page_numbers:
                        current.page_numbers.append(page.page_number)
                continue

            prefix = segments[0][0]
            if prefix.strip():
                if current:
                    current.text = self._join_text(current.text, prefix)
                    if page.page_number not in current.page_numbers:
                        current.page_numbers.append(page.page_number)
                else:
                    current = RegulatoryUnit(
                        text=prefix,
                        page_numbers=[page.page_number],
                        chunk_type="page_preface",
                    )

            for segment_text, marker in segments[1:]:
                if current and len(current.text.strip()) >= self.min_chars:
                    units.append(current)
                marker_title = self._normalize_marker(marker)
                marker_kind = self._marker_kind(marker_title)
                current_path = self._update_structure_path(current_path, marker_title, marker_kind)
                current = RegulatoryUnit(
                    text=segment_text,
                    page_numbers=[page.page_number],
                    chunk_type=marker_kind,
                    title=marker_title,
                    article=marker_title if marker_kind == "article" else None,
                    section=marker_title if marker_kind in {"section", "chapitre", "titre"} else None,
                    structure_path=list(current_path),
                )

        if current and len(current.text.strip()) >= self.min_chars:
            units.append(current)
        return units

    def _segments_for_page(self, text: str) -> list[tuple[str, str | None]]:
        clean = self._normalize_text(text)
        matches = list(self.MARKER_RE.finditer(clean))
        if not matches:
            return []

        first_marker_start = matches[0].start("marker")
        segments: list[tuple[str, str | None]] = [(clean[:first_marker_start].strip(), None)]
        for index, match in enumerate(matches):
            start = match.start("marker")
            end = matches[index + 1].start("marker") if index + 1 < len(matches) else len(clean)
            segment = clean[start:end].strip()
            if segment:
                segments.append((segment, match.group("marker")))
        return segments

    def _split_unit_if_needed(self, unit: RegulatoryUnit) -> list[RegulatoryUnit]:
        clean = self._normalize_text(unit.text)
        if len(clean) <= self.max_chars:
            unit.text = clean
            return [unit]

        split_units: list[RegulatoryUnit] = []
        start = 0
        split_index = 1
        while start < len(clean):
            end = min(start + self.max_chars, len(clean))
            if end < len(clean):
                end = self._best_boundary(clean, start, end)
            chunk_text = clean[start:end].strip()
            if chunk_text:
                split_units.append(
                    RegulatoryUnit(
                        text=chunk_text,
                        page_numbers=list(unit.page_numbers),
                        chunk_type=f"{unit.chunk_type}_part",
                        title=unit.title,
                        article=unit.article,
                        section=unit.section,
                        structure_path=[*unit.structure_path, f"part {split_index}"],
                    )
                )
                split_index += 1
            if end >= len(clean):
                break
            start = max(0, end - self.overlap_chars)
        return split_units

    def _build_chunk(
        self,
        document: CorpusDocument,
        unit: RegulatoryUnit,
        chunk_index: int,
    ) -> KnowledgeChunk:
        chunk_hash = sha256(unit.text.encode("utf-8")).hexdigest()
        page_start = min(unit.page_numbers) if unit.page_numbers else None
        page_end = max(unit.page_numbers) if unit.page_numbers else None
        chunk_id_source = f"{document.document_id}:{page_start}:{chunk_index}:{chunk_hash}"
        chunk_id = f"chunk-{sha256(chunk_id_source.encode('utf-8')).hexdigest()[:24]}"
        metadata = document.metadata
        citation_label = self._citation_label(document, unit)
        return KnowledgeChunk(
            chunk_id=chunk_id,
            text=unit.text,
            metadata=ChunkMetadata(
                vertical=document.vertical,
                domain=document.domain,
                subdomain=document.subdomain,
                site_hierarchy=list(metadata.get("site_hierarchy") or []),
                site_parent_url=metadata.get("site_parent_url"),
                site_sub_subdomain=metadata.get("site_sub_subdomain"),
                site_sub_subdomain_display=metadata.get("site_sub_subdomain_display"),
                document_id=document.document_id,
                document_title=document.title,
                source_url=document.source_url,
                local_path=document.local_path,
                regulation_type=metadata.get("regulation_type"),
                language=document.language,
                source_file=document.local_path,
                page_start=page_start,
                page_end=page_end,
                page_numbers=unit.page_numbers,
                article=unit.article,
                section=unit.section,
                section_title=unit.title,
                chunk_type=unit.chunk_type,
                structure_path=unit.structure_path,
                source_hash=document.source_hash,
                chunk_index=chunk_index,
                chunk_hash=chunk_hash,
                citation_label=citation_label,
            ),
        )

    def _page_unit(self, page: CorpusPage) -> RegulatoryUnit:
        return RegulatoryUnit(
            text=self._normalize_text(page.text),
            page_numbers=[page.page_number],
            chunk_type="page",
        )

    def _best_boundary(self, text: str, start: int, end: int) -> int:
        minimum = start + int(self.max_chars * 0.6)
        for separator in [". ", "; ", "\n", " "]:
            boundary = text.rfind(separator, minimum, end)
            if boundary > minimum:
                return boundary + len(separator)
        return end

    def _update_structure_path(
        self,
        current_path: list[str],
        marker_title: str,
        marker_kind: str,
    ) -> list[str]:
        if marker_kind in {"titre", "chapitre"}:
            return [marker_title]
        if marker_kind == "section":
            base = current_path[:1] if current_path else []
            return [*base, marker_title]
        if marker_kind == "annexe":
            return [marker_title]
        return current_path

    def _marker_kind(self, marker: str) -> str:
        kind = marker.split(maxsplit=1)[0].lower().rstrip(".")
        if kind == "art":
            return "article"
        return kind

    def _normalize_marker(self, marker: str | None) -> str:
        return self._normalize_text(marker or "")

    def _normalize_text(self, text: str) -> str:
        return " ".join(text.split()).strip()

    def _join_text(self, left: str, right: str) -> str:
        return self._normalize_text(f"{left} {right}")

    def _citation_label(self, document: CorpusDocument, unit: RegulatoryUnit) -> str:
        if document.document_type == "page":
            if unit.section:
                return f"{document.title}, {unit.section}"
            return document.title
        pages = sorted(set(unit.page_numbers))
        if not pages:
            return document.title
        if len(pages) == 1:
            page_label = f"p. {pages[0]}"
        else:
            page_label = f"pp. {pages[0]}-{pages[-1]}"
        if unit.article:
            return f"{document.title}, {unit.article}, {page_label}"
        if unit.section:
            return f"{document.title}, {unit.section}, {page_label}"
        return f"{document.title}, {page_label}"
