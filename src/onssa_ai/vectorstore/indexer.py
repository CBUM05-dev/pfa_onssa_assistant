"""Qdrant indexing for embedded regulatory chunks."""

import json
import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from onssa_ai.schemas.embedding import EmbeddedChunk


def stable_point_id(chunk_id: str) -> str:
    """Return a deterministic Qdrant-compatible UUID for a chunk id."""

    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"onssa-ai:{chunk_id}"))


def read_embedded_chunks(path: Path) -> list[EmbeddedChunk]:
    """Read and validate JSONL embedding artifacts."""

    chunks: list[EmbeddedChunk] = []
    seen_chunk_ids: set[str] = set()
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            chunk = EmbeddedChunk.model_validate(json.loads(line))
            if chunk.chunk_id in seen_chunk_ids:
                msg = f"Duplicate chunk_id {chunk.chunk_id!r} at line {line_number}"
                raise ValueError(msg)
            seen_chunk_ids.add(chunk.chunk_id)
            chunks.append(chunk)
    if not chunks:
        msg = f"No embedded chunks found in {path}"
        raise ValueError(msg)
    return chunks


def validate_embedding_dimensions(chunks: Iterable[EmbeddedChunk], expected_size: int) -> None:
    """Fail before upsert if any vector is incompatible with the collection."""

    for chunk in chunks:
        actual_size = len(chunk.embedding)
        if actual_size != expected_size:
            msg = (
                f"Embedding dimension mismatch for {chunk.chunk_id}: "
                f"expected {expected_size}, got {actual_size}"
            )
            raise ValueError(msg)


def build_payload(chunk: EmbeddedChunk) -> dict[str, Any]:
    """Build the searchable and auditable Qdrant payload."""

    payload = chunk.metadata.model_dump(mode="json")
    payload.update(
        {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "embedding_model": chunk.embedding_model,
            "embedding_dimension": chunk.embedding_dimension,
        }
    )
    return payload


class VectorIndexer:
    """Index embedded chunks into Qdrant."""

    def __init__(self, client: QdrantClient, collection_name: str, batch_size: int = 64) -> None:
        self.client = client
        self.collection_name = collection_name
        self.batch_size = batch_size

    def index(self, chunks: list[EmbeddedChunk]) -> int:
        indexed_count = 0
        for start in range(0, len(chunks), self.batch_size):
            batch = chunks[start : start + self.batch_size]
            points = [
                models.PointStruct(
                    id=stable_point_id(chunk.chunk_id),
                    vector=chunk.embedding,
                    payload=build_payload(chunk),
                )
                for chunk in batch
            ]
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )
            indexed_count += len(points)
        return indexed_count
