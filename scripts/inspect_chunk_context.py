"""Inspect citation context from chunks.jsonl without touching the RAG stack."""

import argparse
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_CHUNKS_PATH = Path("data/processed/chunks/chunks.jsonl")
TOKEN_RE = re.compile(r"[a-z0-9]{2,}", re.IGNORECASE)
STOPWORDS = {
    "alors",
    "avec",
    "aux",
    "dans",
    "des",
    "du",
    "elle",
    "est",
    "les",
    "leur",
    "leurs",
    "par",
    "pas",
    "pour",
    "que",
    "qui",
    "quoi",
    "sans",
    "sur",
    "une",
    "vous",
    "comment",
    "quelle",
    "quelles",
    "quels",
    "sont",
}


def configure_output_encoding() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value.lower()


def tokenize(value: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(normalize_text(value)) if token not in STOPWORDS]


def read_chunks(path: Path) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_number"] = line_number
            chunks.append(row)
    if not chunks:
        msg = f"No chunks found in {path}"
        raise ValueError(msg)
    return chunks


def build_document_frequencies(chunks: list[dict[str, Any]]) -> Counter[str]:
    frequencies: Counter[str] = Counter()
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        searchable = " ".join(
            [
                chunk.get("text", ""),
                metadata.get("document_title") or "",
                metadata.get("article") or "",
                metadata.get("section_title") or "",
                metadata.get("citation_label") or "",
            ]
        )
        frequencies.update(set(tokenize(searchable)))
    return frequencies


def score_chunk(
    chunk: dict[str, Any],
    query_tokens: list[str],
    phrase: str,
    document_frequencies: Counter[str],
    document_count: int,
) -> float:
    metadata = chunk.get("metadata", {})
    text = chunk.get("text", "")
    title = metadata.get("document_title") or ""
    structure = " ".join(
        [
            metadata.get("article") or "",
            metadata.get("section_title") or "",
            metadata.get("chunk_type") or "",
        ]
    )
    text_tokens = Counter(tokenize(text))
    metadata_tokens = Counter(tokenize(f"{title} {structure}"))

    score = 0.0
    for token in query_tokens:
        idf = math.log((document_count + 1) / (document_frequencies[token] + 1)) + 1
        score += text_tokens[token] * idf
        score += metadata_tokens[token] * idf * 1.5

    normalized_text = normalize_text(text)
    if phrase and phrase in normalized_text:
        score += 5.0
    return score


def search(chunks: list[dict[str, Any]], question: str, top_k: int) -> list[tuple[float, dict[str, Any]]]:
    query_tokens = tokenize(question)
    if not query_tokens:
        msg = "Question must contain at least one searchable term."
        raise ValueError(msg)
    document_frequencies = build_document_frequencies(chunks)
    phrase = normalize_text(question).strip()
    scored = [
        (
            score_chunk(
                chunk=chunk,
                query_tokens=query_tokens,
                phrase=phrase,
                document_frequencies=document_frequencies,
                document_count=len(chunks),
            ),
            chunk,
        )
        for chunk in chunks
    ]
    return [(score, chunk) for score, chunk in sorted(scored, reverse=True, key=lambda item: item[0])[:top_k] if score > 0]


def compact_text(value: str, max_chars: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


def print_results(question: str, results: list[tuple[float, dict[str, Any]]], max_chars: int) -> None:
    print(f"Question: {question}")
    print("Mode: lexical debug over chunks.jsonl, not final semantic RAG")
    if not results:
        print("\nNo evidence-like context found.")
        return

    for index, (score, chunk) in enumerate(results, start=1):
        metadata = chunk.get("metadata", {})
        pages = metadata.get("page_numbers") or []
        pages_label = ", ".join(str(page) for page in pages) if pages else "n/a"
        print("\n" + "=" * 88)
        print(f"#{index} score={score:.3f} chunk_id={chunk.get('chunk_id')}")
        print(f"Citation: {metadata.get('citation_label')}")
        print(f"Document: {metadata.get('document_title')}")
        print(f"Type: {metadata.get('regulation_type')} | Chunk: {metadata.get('chunk_type')} | Pages: {pages_label}")
        if metadata.get("article") or metadata.get("section_title"):
            print(f"Structure: {metadata.get('article') or ''} {metadata.get('section_title') or ''}".strip())
        print(f"Source: {metadata.get('source_url')}")
        print("-" * 88)
        print(compact_text(chunk.get("text", ""), max_chars=max_chars))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask a question and inspect matching contexts from chunks.jsonl."
    )
    parser.add_argument("question", nargs="*", help="Question to inspect.")
    parser.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS_PATH)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-chars", type=int, default=900)
    return parser.parse_args()


def main() -> None:
    configure_output_encoding()
    args = parse_args()
    question = " ".join(args.question).strip()
    if not question:
        question = input("Question: ").strip()
    chunks = read_chunks(args.chunks)
    results = search(chunks=chunks, question=question, top_k=args.top_k)
    print_results(question=question, results=results, max_chars=args.max_chars)


if __name__ == "__main__":
    main()
