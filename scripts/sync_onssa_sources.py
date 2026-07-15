"""Synchronize ONSSA source pages and PDFs."""

import argparse
from pathlib import Path

from onssa_ai.sources.config import load_sources_config
from onssa_ai.sources.sync import SourceSyncService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronize ONSSA public sources.")
    parser.add_argument(
        "--config",
        default="configs/sources.yaml",
        help="Path to the sources YAML configuration.",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Optional source name to synchronize. Defaults to all configured sources.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_sources_config(Path(args.config))
    selected_sources = [
        source for source in config.sources if args.source is None or source.name == args.source
    ]
    if not selected_sources:
        raise SystemExit(f"No source matched: {args.source}")

    for source in selected_sources:
        summary = SourceSyncService(source).sync()
        print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
