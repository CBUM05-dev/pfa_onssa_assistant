"""Report unresolved guides, annexes, and legal references in chunk metadata."""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from onssa_ai.schemas.chunk import KnowledgeChunk


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report reference graph data-quality issues.")
    parser.add_argument(
        "--chunks",
        default="data/processed/chunks/chunks.jsonl",
        help="Path to chunks JSONL produced by scripts/build_chunks.py.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/chunks/reference_quality_report.json",
        help="Path to write the JSON report.",
    )
    return parser.parse_args()


def read_chunks(path: Path) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                chunks.append(KnowledgeChunk.model_validate_json(line))
    return chunks


def build_report(chunks: list[KnowledgeChunk]) -> dict[str, Any]:
    unresolved: list[dict[str, Any]] = []
    missing_content_notices: list[dict[str, Any]] = []
    answer_roles = Counter(chunk.metadata.answer_role for chunk in chunks)

    for chunk in chunks:
        metadata = chunk.metadata
        for reference in metadata.outgoing_references:
            if reference.missing:
                row = {
                    "chunk_id": chunk.chunk_id,
                    "citation_label": metadata.citation_label,
                    "reference_type": reference.reference_type,
                    "document_number": reference.document_number,
                    "article_number": reference.article_number,
                    "raw_text": reference.raw_text,
                }
                unresolved.append(row)
                if reference.reference_type == "annex_or_guide_content":
                    missing_content_notices.append(row)

    return {
        "chunk_count": len(chunks),
        "answer_roles": dict(answer_roles),
        "unresolved_reference_count": len(unresolved),
        "missing_guide_or_annex_content_count": len(missing_content_notices),
        "unresolved_references": unresolved,
        "missing_guide_or_annex_content": missing_content_notices,
    }


def main() -> None:
    args = parse_args()
    chunks_path = Path(args.chunks)
    output_path = Path(args.output)
    report = build_report(read_chunks(chunks_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
