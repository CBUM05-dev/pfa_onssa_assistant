"""Extract and resolve legal references from ONSSA regulatory chunks."""

import re
from collections import defaultdict

from onssa_ai.schemas.chunk import ChunkMetadata, KnowledgeChunk
from onssa_ai.schemas.reference import LegalReference


DOCUMENT_RE = re.compile(
    r"\b(?P<type>loi|decret|décret|arrete|arrêté|decision|décision)"
    r"(?:\s+n[°o]\s*|\s+num[eé]ro\s*|\s+)?"
    r"(?P<number>\d{1,4}[-/]\d{1,4}(?:[-/]\d{1,4})?)",
    re.IGNORECASE,
)
ARTICLE_RE = re.compile(r"\barticle\s+(?P<number>\d+(?:[-.]\d+)?)\b", re.IGNORECASE)
ARTICLE_HEADER_RE = re.compile(r"^\s*article\s+(?P<number>\d+(?:[-.]\d+)?)\b", re.IGNORECASE)
CODEX_RE = re.compile(r"\bCodex\s+Alimentarius\b", re.IGNORECASE)
ANNEX_NOTICE_RE = re.compile(
    r"\b(annex[eé]\s+(?:a|à)\s+l['’]original|annex[eé]\s+au\s+present|"
    r"approuv[eé]\s+tel\s+qu['’]il\s+est\s+annex[eé]|guide\s+.*\bapprouv[eé])\b",
    re.IGNORECASE,
)

TYPE_ALIASES = {
    "décret": "decret",
    "decret": "decret",
    "loi": "loi",
    "arrêté": "arrete",
    "arrete": "arrete",
    "décision": "decision",
    "decision": "decision",
}

DIRECT_ANSWER_ROLES = {"direct_answer", "substantive_rule", "guide_content"}


def extract_document_number(*texts: str | None) -> str | None:
    """Return the first legal document number found in metadata or text."""

    for text in texts:
        if not text:
            continue
        match = DOCUMENT_RE.search(text)
        if match:
            return normalize_number(match.group("number"))
    return None


def extract_article_number(article: str | None, text: str | None = None) -> str | None:
    """Return a normalized article number from a chunk marker or text."""

    if article:
        match = ARTICLE_RE.search(article)
        if match:
            return normalize_number(match.group("number"))
    if text:
        match = ARTICLE_HEADER_RE.search(text)
        if match:
            return normalize_number(match.group("number"))
    return None


def extract_references(text: str) -> list[LegalReference]:
    """Extract outgoing legal references from free text."""

    references: list[LegalReference] = []
    seen: set[tuple[str, str | None, str | None, str]] = set()

    for match in DOCUMENT_RE.finditer(text):
        window = text[max(0, match.start() - 140) : min(len(text), match.end() + 140)]
        article_match = ARTICLE_RE.search(window)
        reference = LegalReference(
            reference_type=normalize_type(match.group("type")),
            document_number=normalize_number(match.group("number")),
            article_number=normalize_number(article_match.group("number"))
            if article_match
            else None,
            raw_text=match.group(0),
        )
        key = (
            reference.reference_type,
            reference.document_number,
            reference.article_number,
            reference.raw_text.lower(),
        )
        if key not in seen:
            references.append(reference)
            seen.add(key)

    for match in CODEX_RE.finditer(text):
        references.append(
            LegalReference(reference_type="codex", raw_text=match.group(0), missing=True)
        )

    if ANNEX_NOTICE_RE.search(text):
        references.append(
            LegalReference(
                reference_type="annex_or_guide_content",
                raw_text=ANNEX_NOTICE_RE.search(text).group(0),  # type: ignore[union-attr]
                missing=True,
            )
        )
    return references


def enrich_chunks_with_references(chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
    """Populate reference metadata and resolve links between chunks."""

    for chunk in chunks:
        metadata = chunk.metadata
        metadata.document_number = extract_document_number(
            metadata.document_id,
            metadata.document_title,
            chunk.text[:400],
        )
        metadata.article_number = extract_article_number(metadata.article, chunk.text[:120])
        metadata.document_scope = classify_document_scope(metadata.document_title, chunk.text)
        metadata.answer_role = classify_answer_role(chunk.text, metadata.chunk_type)
        metadata.outgoing_references = [
            reference
            for reference in extract_references(chunk.text)
            if not is_self_reference(reference, metadata)
        ]
        metadata.incoming_references = []

    index = build_reference_index(chunks)
    incoming: dict[str, list[LegalReference]] = defaultdict(list)
    for chunk in chunks:
        resolved_refs: list[LegalReference] = []
        for reference in chunk.metadata.outgoing_references:
            resolved_chunk_id = resolve_reference(reference, index)
            resolved = reference.model_copy(
                update={
                    "resolved_chunk_id": resolved_chunk_id,
                    "missing": reference.missing or resolved_chunk_id is None,
                }
            )
            resolved_refs.append(resolved)
            if resolved_chunk_id:
                incoming[resolved_chunk_id].append(
                    resolved.model_copy(update={"resolved_chunk_id": chunk.chunk_id})
                )
        chunk.metadata.outgoing_references = resolved_refs

    for chunk in chunks:
        chunk.metadata.incoming_references = incoming.get(chunk.chunk_id, [])

    return chunks


def build_reference_index(chunks: list[KnowledgeChunk]) -> dict[tuple[str, str, str | None], str]:
    """Build a lookup from document type/number/article to chunk id."""

    index: dict[tuple[str, str, str | None], str] = {}
    for chunk in chunks:
        document_type = infer_type_from_text(chunk.metadata.document_title) or normalize_type(
            chunk.metadata.regulation_type or ""
        )
        document_number = chunk.metadata.document_number
        if not document_type or not document_number:
            continue
        article_number = chunk.metadata.article_number
        index.setdefault((document_type, document_number, article_number), chunk.chunk_id)
        index.setdefault((document_type, document_number, None), chunk.chunk_id)
    return index


def resolve_reference(
    reference: LegalReference,
    index: dict[tuple[str, str, str | None], str],
) -> str | None:
    """Resolve a reference to a known chunk id when possible."""

    if not reference.document_number:
        return None
    typed_key = (
        reference.reference_type,
        reference.document_number,
        reference.article_number,
    )
    fallback_key = (reference.reference_type, reference.document_number, None)
    return index.get(typed_key) or index.get(fallback_key)


def is_self_reference(reference: LegalReference, metadata: ChunkMetadata) -> bool:
    """Return true when a detected legal reference only identifies its own document."""

    if not reference.document_number or reference.document_number != metadata.document_number:
        return False
    document_type = infer_type_from_text(metadata.document_title) or normalize_type(
        metadata.regulation_type or ""
    )
    return bool(document_type and reference.reference_type == document_type)


def classify_document_scope(title: str, text: str) -> str:
    value = f"{title} {text[:600]}".lower()
    if "guide" in value and ("bonne pratique" in value or "bonnes pratiques" in value):
        return "guide"
    if "codex alimentarius" in value:
        return "codex"
    document_type = infer_type_from_text(value)
    return document_type or "regulatory_text"


def classify_answer_role(text: str, chunk_type: str) -> str:
    value = text.lower()
    if ANNEX_NOTICE_RE.search(text):
        return "missing_content"
    if "approuv" in value and "guide" in value:
        return "approval_reference"
    if "vu la loi" in value or "vu le decret" in value or "vu le décret" in value:
        return "legal_basis"
    if chunk_type in {"article", "article_part"}:
        return "substantive_rule"
    if "guide" in value and ("bonne pratique" in value or "bonnes pratiques" in value):
        return "guide_content"
    return "direct_answer"


def normalize_type(value: str) -> str:
    return TYPE_ALIASES.get(value.strip().lower(), value.strip().lower())


def normalize_number(value: str) -> str:
    return value.strip().replace("/", "-")


def infer_type_from_text(text: str) -> str | None:
    match = re.search(r"\b(loi|decret|décret|arrete|arrêté|decision|décision)\b", text, re.I)
    if not match:
        return None
    return normalize_type(match.group(1))
