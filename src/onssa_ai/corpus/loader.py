"""Knowledge corpus loading."""

import json
from pathlib import Path

from onssa_ai.schemas.corpus import KnowledgeCorpus


class CorpusLoader:
    """Load the generated ONSSA knowledge corpus from disk."""

    def load(self, path: Path) -> KnowledgeCorpus:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):
            data = {"documents": data}
        return KnowledgeCorpus.model_validate(data)
