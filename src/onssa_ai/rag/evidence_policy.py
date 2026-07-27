"""Evidence sufficiency policy."""

from onssa_ai.core.config import RetrievalConfig
from onssa_ai.schemas.retrieval import RetrievedChunk

DIRECT_ANSWER_ROLES = {"direct_answer", "substantive_rule", "guide_content"}


class EvidencePolicy:
    """Decide whether retrieved evidence is sufficient for a grounded answer."""

    def __init__(self, config: RetrievalConfig) -> None:
        self.config = config

    def is_sufficient(self, evidence: list[RetrievedChunk]) -> bool:
        if not evidence:
            return False
        direct_evidence = [
            item for item in evidence if item.chunk.metadata.answer_role in DIRECT_ANSWER_ROLES
        ]
        if not direct_evidence:
            return False
        return any(self._score(item) >= self._threshold(item) for item in direct_evidence)

    def _score(self, item: RetrievedChunk) -> float:
        return item.rerank_score if item.rerank_score is not None else item.score

    def _threshold(self, item: RetrievedChunk) -> float:
        metadata = item.chunk.metadata
        chunk_type_threshold = self.config.min_rerank_score_by_chunk_type.get(
            metadata.chunk_type
        )
        if chunk_type_threshold is not None:
            return chunk_type_threshold
        vertical_threshold = self.config.min_rerank_score_by_vertical.get(metadata.vertical)
        if vertical_threshold is not None:
            return vertical_threshold
        return self.config.min_rerank_score
