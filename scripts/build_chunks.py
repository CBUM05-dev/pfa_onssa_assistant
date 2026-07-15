"""Validate knowledge corpus and build citation-safe chunks."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from onssa_ai.corpus.chunker import CorpusChunker
from onssa_ai.corpus.loader import CorpusLoader
from onssa_ai.corpus.validator import CorpusValidator


class ChunkingConfig(BaseModel):
    corpus_path: Path
    output_path: Path
    report_path: Path
    strategy: str = "structure_aware"
    max_chars: int = 1600
    overlap_chars: int = 250
    min_chars: int = 120
    prefer_structure_boundaries: bool = True
    structural_markers: list[str] = []
    require_domain: str | None = None
    require_subdomain: str | None = None
    fail_on_unclassified: bool = True


class ChunkingReport(BaseModel):
    generated_at: str
    corpus_path: str
    output_path: str
    document_count: int
    chunk_count: int
    strategy: str
    max_chars: int
    overlap_chars: int
    min_chars: int
    prefer_structure_boundaries: bool
    require_domain: str | None
    require_subdomain: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build chunks from knowledge_corpus.json.")
    parser.add_argument(
        "--config",
        default="configs/chunking.yaml",
        help="Path to chunking YAML configuration.",
    )
    return parser.parse_args()


def load_config(path: Path) -> ChunkingConfig:
    with path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = yaml.safe_load(file) or {}
    return ChunkingConfig.model_validate(data.get("chunking", {}))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False))
            file.write("\n")


def write_report(path: Path, report: ChunkingReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(report.model_dump(mode="json"), file, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config))
    corpus = CorpusLoader().load(config.corpus_path)
    CorpusValidator().validate(
        corpus,
        require_domain=config.require_domain,
        require_subdomain=config.require_subdomain,
        fail_on_unclassified=config.fail_on_unclassified,
    )
    chunks = CorpusChunker(
        max_chars=config.max_chars,
        overlap_chars=config.overlap_chars,
        min_chars=config.min_chars,
        strategy=config.strategy,
        prefer_structure_boundaries=config.prefer_structure_boundaries,
    ).build_chunks(corpus)
    write_jsonl(config.output_path, [chunk.model_dump(mode="json") for chunk in chunks])
    report = ChunkingReport(
        generated_at=datetime.now(UTC).isoformat(),
        corpus_path=str(config.corpus_path),
        output_path=str(config.output_path),
        document_count=len(corpus.documents),
        chunk_count=len(chunks),
        strategy=config.strategy,
        max_chars=config.max_chars,
        overlap_chars=config.overlap_chars,
        min_chars=config.min_chars,
        prefer_structure_boundaries=config.prefer_structure_boundaries,
        require_domain=config.require_domain,
        require_subdomain=config.require_subdomain,
    )
    write_report(config.report_path, report)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
