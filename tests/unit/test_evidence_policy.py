from onssa_ai.core.config import RetrievalConfig
from onssa_ai.rag.evidence_policy import EvidencePolicy


def test_empty_evidence_is_insufficient() -> None:
    config = RetrievalConfig(
        vertical="regulation",
        domain="transversal_regulation",
        subdomain="food_safety",
        top_k_initial=30,
        top_k_reranked=8,
        min_retrieval_score=0.45,
        min_rerank_score=0.2,
    )
    assert EvidencePolicy(config).is_sufficient([]) is False
