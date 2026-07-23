"""Merge multiple chunk JSONL files into one validated artifact."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from onssa_ai.schemas.chunk import KnowledgeChunk


class MergeReport(BaseModel):
    generated_at: str
    input_paths: list[str]
    output_path: str
    report_path: str
    input_counts: dict[str, int] = Field(default_factory=dict)
    merged_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge validated chunk JSONL files.")
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input chunks JSONL path. Pass once per file.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/chunks/chunks_all.jsonl",
        help="Merged chunks JSONL output path.",
    )
    parser.add_argument(
        "--report-path",
        default="data/processed/chunks/chunks_all_report.json",
        help="Merge report JSON path.",
    )
    return parser.parse_args()


def read_chunks(path: Path) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                chunks.append(KnowledgeChunk.model_validate(json.loads(line)))
            except Exception as exc:
                msg = f"Invalid chunk in {path} at line {line_number}: {exc}"
                raise ValueError(msg) from exc
    if not chunks:
        msg = f"No chunks found in {path}"
        raise ValueError(msg)
    return chunks


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def write_jsonl(path: Path, chunks: list[KnowledgeChunk]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk.model_dump(mode="json"), ensure_ascii=False))
            file.write("\n")


def main() -> None:
    args = parse_args()
    input_paths = [Path(value) for value in args.input]
    output_path = Path(args.output)
    report_path = Path(args.report_path)
    merged: list[KnowledgeChunk] = []
    input_counts: dict[str, int] = {}
    seen_chunk_ids: set[str] = set()

    for input_path in input_paths:
        chunks = read_chunks(input_path)
        input_counts[str(input_path)] = len(chunks)
        for chunk in chunks:
            if chunk.chunk_id in seen_chunk_ids:
                msg = f"Duplicate chunk_id {chunk.chunk_id!r} from {input_path}"
                raise ValueError(msg)
            seen_chunk_ids.add(chunk.chunk_id)
            merged.append(chunk)

    write_jsonl(output_path, merged)
    report = MergeReport(
        generated_at=datetime.now(UTC).isoformat(),
        input_paths=[str(path) for path in input_paths],
        output_path=str(output_path),
        report_path=str(report_path),
        input_counts=input_counts,
        merged_count=len(merged),
    )
    write_json(report_path, report.model_dump(mode="json"))
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
