"""Index embedded chunks into Qdrant."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from onssa_ai.core.config import QdrantConfig
from onssa_ai.vectorstore.collection_manager import QdrantCollectionManager
from onssa_ai.vectorstore.indexer import (
    VectorIndexer,
    read_embedded_chunks,
    validate_embedding_dimensions,
)
from onssa_ai.vectorstore.qdrant_client import build_qdrant_client


class QdrantIndexConfig(BaseModel):
    embeddings_path: Path
    report_path: Path = Path("data/processed/embeddings/qdrant_index_report.json")
    batch_size: int = Field(default=64, ge=1)


class QdrantIndexReport(BaseModel):
    generated_at: str
    embeddings_path: str
    collection_name: str
    vector_size: int
    batch_size: int
    chunk_count: int
    indexed_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Index embedded chunks into Qdrant.")
    parser.add_argument(
        "--embeddings-config",
        default="configs/embeddings.yaml",
        help="Path to embeddings YAML configuration.",
    )
    parser.add_argument(
        "--qdrant-config",
        default="configs/qdrant.yaml",
        help="Path to Qdrant YAML configuration.",
    )
    parser.add_argument(
        "--report-path",
        default="data/processed/embeddings/qdrant_index_report.json",
        help="Path for the indexing report.",
    )
    parser.add_argument(
        "--qdrant-host",
        default=None,
        help="Override Qdrant host. Use 127.0.0.1 when running this script from PowerShell.",
    )
    parser.add_argument(
        "--qdrant-port",
        type=int,
        default=None,
        help="Override Qdrant port.",
    )
    parser.add_argument("--batch-size", type=int, default=64, help="Qdrant upsert batch size.")
    parser.add_argument(
        "--recreate-collection",
        action="store_true",
        help="Delete and recreate the target collection before indexing.",
    )
    return parser.parse_args()


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}
    if not isinstance(loaded, dict):
        msg = f"Expected YAML mapping in {path}"
        raise ValueError(msg)
    return loaded


def load_index_config(args: argparse.Namespace) -> QdrantIndexConfig:
    embeddings_yaml = read_yaml(Path(args.embeddings_config))
    embeddings_data = embeddings_yaml.get("embeddings", {})
    return QdrantIndexConfig(
        embeddings_path=embeddings_data["output_path"],
        report_path=args.report_path,
        batch_size=args.batch_size,
    )


def load_qdrant_config(path: Path, args: argparse.Namespace) -> QdrantConfig:
    qdrant_yaml = read_yaml(path)
    qdrant_data = qdrant_yaml.get("qdrant", {})
    if args.qdrant_host:
        qdrant_data["host"] = args.qdrant_host
    if args.qdrant_port:
        qdrant_data["port"] = args.qdrant_port
    return QdrantConfig(**qdrant_data)


def write_report(path: Path, report: QdrantIndexReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(report.model_dump(mode="json"), file, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()
    index_config = load_index_config(args)
    qdrant_config = load_qdrant_config(Path(args.qdrant_config), args)

    chunks = read_embedded_chunks(index_config.embeddings_path)
    validate_embedding_dimensions(chunks, qdrant_config.vector_size)

    client = build_qdrant_client(qdrant_config)
    if args.recreate_collection and client.collection_exists(qdrant_config.collection_name):
        client.delete_collection(qdrant_config.collection_name)
    QdrantCollectionManager(client, qdrant_config).ensure_collection()
    indexed_count = VectorIndexer(
        client=client,
        collection_name=qdrant_config.collection_name,
        batch_size=index_config.batch_size,
    ).index(chunks)

    report = QdrantIndexReport(
        generated_at=datetime.now(UTC).isoformat(),
        embeddings_path=str(index_config.embeddings_path),
        collection_name=qdrant_config.collection_name,
        vector_size=qdrant_config.vector_size,
        batch_size=index_config.batch_size,
        chunk_count=len(chunks),
        indexed_count=indexed_count,
    )
    write_report(index_config.report_path, report)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
