"""Validate the generated ONSSA knowledge corpus."""

from pathlib import Path

from onssa_ai.corpus.loader import CorpusLoader
from onssa_ai.corpus.validator import CorpusValidator
from onssa_ai.core.config import get_settings


def main() -> None:
    settings = get_settings()
    corpus_path = Path(settings.paths.corpus_path)
    corpus = CorpusLoader().load(corpus_path)
    CorpusValidator().validate(corpus)
    print(f"Corpus valid: {len(corpus.documents)} documents")


if __name__ == "__main__":
    main()
