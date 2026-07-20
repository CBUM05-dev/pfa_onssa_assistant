from onssa_ai.core.config import RetrievalConfig
from onssa_ai.rag.evidence_policy import EvidencePolicy
from onssa_ai.schemas.chunk import ChunkMetadata, KnowledgeChunk
from onssa_ai.schemas.retrieval import RetrievedChunk


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


def test_approval_only_evidence_is_insufficient() -> None:
    config = _config()
    evidence = [_retrieved_chunk(answer_role="approval_reference", score=0.9)]

    assert EvidencePolicy(config).is_sufficient(evidence) is False


def test_direct_answer_role_with_good_score_is_sufficient() -> None:
    config = _config()
    evidence = [_retrieved_chunk(answer_role="substantive_rule", score=0.9)]

    assert EvidencePolicy(config).is_sufficient(evidence) is True


def _config() -> RetrievalConfig:
    return RetrievalConfig(
        vertical="regulation",
        domain="transversal_regulation",
        subdomain="food_safety",
        top_k_initial=30,
        top_k_reranked=8,
        min_retrieval_score=0.45,
        min_rerank_score=0.2,
    )


def _retrieved_chunk(answer_role: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=KnowledgeChunk(
            chunk_id="chunk-test",
            text="Article 1. Les exploitants doivent respecter les exigences sanitaires.",
            metadata=ChunkMetadata(
                vertical="regulation",
                domain="transversal_regulation",
                subdomain="food_safety",
                document_id="doc-test",
                document_title="Décret test",
                chunk_index=0,
                chunk_hash="hash",
                citation_label="Décret test, Article 1",
                answer_role=answer_role,
            ),
        ),
        score=score,
    )
