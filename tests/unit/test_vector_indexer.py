import json
from pathlib import Path

import pytest

from onssa_ai.vectorstore.indexer import (
    build_payload,
    read_embedded_chunks,
    stable_point_id,
    validate_embedding_dimensions,
)


def embedded_chunk_row(chunk_id: str = "chunk-1", dimension: int = 3) -> dict:
    return {
        "chunk_id": chunk_id,
        "text": "Texte reglementaire ONSSA.",
        "metadata": {
            "vertical": "food_safety",
            "domain": "reglementation_transversale",
            "subdomain": "securite_sanitaire",
            "document_id": "doc-1",
            "document_title": "Document ONSSA",
            "chunk_index": 0,
            "chunk_hash": "abc123",
            "citation_label": "Document ONSSA",
        },
        "embedding": [0.1] * dimension,
        "embedding_model": "BAAI/bge-m3",
        "embedding_dimension": dimension,
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(f"{json.dumps(row, ensure_ascii=False)}\n" for row in rows),
        encoding="utf-8",
    )


def test_read_embedded_chunks_validates_duplicate_chunk_ids(tmp_path: Path) -> None:
    path = tmp_path / "embeddings.jsonl"
    write_jsonl(path, [embedded_chunk_row("same"), embedded_chunk_row("same")])

    with pytest.raises(ValueError, match="Duplicate chunk_id"):
        read_embedded_chunks(path)


def test_validate_embedding_dimensions_rejects_wrong_size(tmp_path: Path) -> None:
    path = tmp_path / "embeddings.jsonl"
    write_jsonl(path, [embedded_chunk_row(dimension=2)])
    chunks = read_embedded_chunks(path)

    with pytest.raises(ValueError, match="Embedding dimension mismatch"):
        validate_embedding_dimensions(chunks, expected_size=3)


def test_payload_preserves_text_and_citation_metadata(tmp_path: Path) -> None:
    path = tmp_path / "embeddings.jsonl"
    write_jsonl(path, [embedded_chunk_row()])
    chunk = read_embedded_chunks(path)[0]

    payload = build_payload(chunk)

    assert payload["chunk_id"] == "chunk-1"
    assert payload["text"] == "Texte reglementaire ONSSA."
    assert payload["citation_label"] == "Document ONSSA"
    assert payload["embedding_model"] == "BAAI/bge-m3"
    assert stable_point_id("chunk-1") == stable_point_id("chunk-1")
