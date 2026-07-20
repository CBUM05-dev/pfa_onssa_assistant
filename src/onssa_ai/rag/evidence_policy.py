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
        if not any(item.chunk.metadata.answer_role in DIRECT_ANSWER_ROLES for item in evidence):
            return False
        best_score = max(
            item.rerank_score if item.rerank_score is not None else item.score
            for item in evidence
        )
        return best_score >= self.config.min_rerank_score
