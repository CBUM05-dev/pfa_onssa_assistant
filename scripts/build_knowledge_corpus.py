"""Build data/corpus/knowledge_corpus.json from synchronized ONSSA sources."""

import argparse
from pathlib import Path
from typing import Any

import yaml

from onssa_ai.ingestion.corpus_builder import CorpusBuilder, CorpusBuildConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ONSSA knowledge corpus.")
    parser.add_argument(
        "--config",
        default="configs/corpus.yaml",
        help="Path to corpus builder YAML configuration.",
    )
    parser.add_argument(
        "--include-pages",
        action="store_true",
        help="Also include downloaded HTML pages in the corpus.",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include all processable sources instead of only first-slice relevant sources.",
    )
    return parser.parse_args()


def load_config(path: Path, include_pages: bool, include_all: bool) -> CorpusBuildConfig:
    with path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = yaml.safe_load(file) or {}
    corpus_data = data.get("corpus", {})
    if include_pages:
        corpus_data["include_pages"] = True
    if include_all:
        corpus_data["include_all_sources"] = True
    return CorpusBuildConfig.model_validate(corpus_data)


def main() -> None:
    args = parse_args()
    config = load_config(Path(args.config), args.include_pages, args.include_all)
    report = CorpusBuilder(config).build()
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
