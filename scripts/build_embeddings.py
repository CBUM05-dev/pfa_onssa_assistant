"""Build local BAAI/bge-m3 embeddings for validated chunks."""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from onssa_ai.embeddings.batcher import batched
from onssa_ai.embeddings.bge_m3 import BgeM3Embedder
from onssa_ai.schemas.chunk import KnowledgeChunk
from onssa_ai.schemas.embedding import EmbeddedChunk


class EmbeddingConfig(BaseModel):
    input_path: Path
    output_path: Path
    report_path: Path
    model_name: str = "BAAI/bge-m3"
    device: str = "auto"
    batch_size: int = Field(default=8, ge=1)
    vector_size: int = Field(default=1024, ge=1)
    normalize_embeddings: bool = True
    local_files_only: bool = True
    cache_dir: Path | None = None
    text_prefix: str = ""
    overwrite: bool = True


class EmbeddingReport(BaseModel):
    generated_at: str
    input_path: str
    output_path: str
    model_name: str
    device: str
    batch_size: int
    vector_size: int
    normalize_embeddings: bool
    local_files_only: bool
    chunk_count: int
    embedding_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build bge-m3 embeddings from chunks.jsonl.")
    parser.add_argument(
        "--config",
        default="configs/embeddings.yaml",
        help="Path to embeddings YAML configuration.",
    )
    return parser.parse_args()


def load_config(path: Path) -> EmbeddingConfig:
    with path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = yaml.safe_load(file) or {}
    return EmbeddingConfig.model_validate(data.get("embeddings", {}))


def read_chunks(path: Path) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    seen_chunk_ids: set[str] = set()
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            chunk = KnowledgeChunk.model_validate(json.loads(line))
            if chunk.chunk_id in seen_chunk_ids:
                msg = f"Duplicate chunk_id {chunk.chunk_id!r} at line {line_number}"
                raise ValueError(msg)
            seen_chunk_ids.add(chunk.chunk_id)
            chunks.append(chunk)
    if not chunks:
        msg = f"No chunks found in {path}"
        raise ValueError(msg)
    return chunks


def validate_vector(vector: list[float], expected_size: int, chunk_id: str) -> None:
    if len(vector) != expected_size:
        msg = (
            f"Embedding dimension mismatch for {chunk_id}: "
            f"expected {expected_size}, got {len(vector)}"
        )
        raise ValueError(msg)


def write_report(path: Path, report: EmbeddingReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(report.model_dump(mode="json"), file, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))
    if config.output_path.exists() and not config.overwrite:
        msg = f"Output already exists and overwrite=false: {config.output_path}"
        raise FileExistsError(msg)

    chunks = read_chunks(config.input_path)
    embedder = BgeM3Embedder(
        model_name=config.model_name,
        device=config.device,
        cache_dir=config.cache_dir,
        local_files_only=config.local_files_only,
        normalize_embeddings=config.normalize_embeddings,
    )

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_output_path = config.output_path.with_suffix(config.output_path.suffix + ".tmp")
    embedding_count = 0
    try:
        with temp_output_path.open("w", encoding="utf-8") as file:
            for batch in batched(chunks, config.batch_size):
                texts = [f"{config.text_prefix}{chunk.text}" for chunk in batch]
                vectors = embedder.embed_texts(texts)
                if len(vectors) != len(batch):
                    msg = f"Expected {len(batch)} embeddings, got {len(vectors)}"
                    raise ValueError(msg)
                for chunk, vector in zip(batch, vectors, strict=True):
                    validate_vector(vector, config.vector_size, chunk.chunk_id)
                    row = EmbeddedChunk(
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        metadata=chunk.metadata,
                        embedding=vector,
                        embedding_model=config.model_name,
                        embedding_dimension=config.vector_size,
                    )
                    file.write(json.dumps(row.model_dump(mode="json"), ensure_ascii=False))
                    file.write("\n")
                    embedding_count += 1
        temp_output_path.replace(config.output_path)
    except Exception:
        temp_output_path.unlink(missing_ok=True)
        raise

    report = EmbeddingReport(
        generated_at=datetime.now(UTC).isoformat(),
        input_path=str(config.input_path),
        output_path=str(config.output_path),
        model_name=config.model_name,
        device=config.device,
        batch_size=config.batch_size,
        vector_size=config.vector_size,
        normalize_embeddings=config.normalize_embeddings,
        local_files_only=config.local_files_only,
        chunk_count=len(chunks),
        embedding_count=embedding_count,
    )
    write_report(config.report_path, report)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
