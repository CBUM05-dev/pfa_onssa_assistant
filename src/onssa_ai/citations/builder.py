"""Citation construction from retrieved evidence."""

import re
import unicodedata

from onssa_ai.schemas.citation import Citation
from onssa_ai.schemas.retrieval import RetrievedChunk

MAX_QUOTE_CHARS = 500
MIN_TOKEN_LENGTH = 4
STOPWORDS = {
    "avec",
    "dans",
    "des",
    "donc",
    "elle",
    "est",
    "les",
    "leur",
    "pour",
    "que",
    "qui",
    "une",
}


class CitationBuilder:
    """Create citation objects from chunk metadata."""

    def build(self, evidence: list[RetrievedChunk], question: str | None = None) -> list[Citation]:
        citations: list[Citation] = []
        for item in evidence:
            metadata = item.chunk.metadata
            citations.append(
                Citation(
                    document_id=metadata.document_id,
                    document_title=metadata.document_title,
                    source_file=metadata.source_file,
                    page=metadata.page_start,
                    article=metadata.article,
                    section=metadata.section,
                    chunk_id=item.chunk.chunk_id,
                    quote=best_quote(item.chunk.text, question),
                )
            )
        return citations


def best_quote(text: str, question: str | None = None, max_chars: int = MAX_QUOTE_CHARS) -> str:
    """Return a compact evidence excerpt, preferably around the user's question terms."""

    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean

    query_tokens = significant_tokens(question or "")
    if not query_tokens:
        return clean[:max_chars]

    best_start = 0
    best_score = -1
    step = max(80, max_chars // 4)
    for start in range(0, max(1, len(clean) - max_chars + 1), step):
        window = clean[start : start + max_chars]
        normalized_window = normalize_text(window)
        score = sum(normalized_window.count(token) for token in query_tokens)
        if re.search(r"\b\d+\s*jours?\b", normalized_window):
            score += 3
        if "delai" in normalized_window:
            score += 2
        if score > best_score:
            best_score = score
            best_start = start

    quote = clean[best_start : best_start + max_chars].strip()
    return trim_to_sentence_boundary(quote)


def significant_tokens(text: str) -> set[str]:
    normalized = normalize_text(text)
    return {
        token
        for token in re.findall(r"\b[a-z0-9]+\b", normalized)
        if len(token) >= MIN_TOKEN_LENGTH and token not in STOPWORDS
    }


def normalize_text(text: str) -> str:
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(char)
    )
    return without_accents


def trim_to_sentence_boundary(text: str) -> str:
    start_match = re.search(r"\b(?:ART\.?\s*\d+|ARTICLE\s+(?:PREMIER|\d+))\b", text, re.I)
    if start_match:
        text = text[start_match.start() :]
    last_boundary = max(text.rfind(". "), text.rfind("; "))
    if last_boundary > len(text) * 0.55:
        return text[: last_boundary + 1].strip()
    return text.strip()
