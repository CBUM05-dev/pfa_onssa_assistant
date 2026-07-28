from onssa_ai.core.config import QueryRoutingRule, RagConfig, RetrievalConfig
from onssa_ai.rag.evidence_policy import EvidencePolicy
from onssa_ai.rag.service import RagService
from onssa_ai.schemas.rag import RagRequest


def test_rag_service_routes_glossary_question_to_site_subdomain() -> None:
    service = _service()

    filters = service._resolve_filters(  # noqa: SLF001
        RagRequest(question="Quelle est la definition de la tracabilite ?")
    )

    assert filters.vertical == "institutionnel"
    assert filters.domain == "onssa"
    assert filters.subdomain == "presentation"
    assert filters.site_sub_subdomain == "glossaire"


def test_explicit_request_filter_overrides_routing() -> None:
    service = _service()

    filters = service._resolve_filters(  # noqa: SLF001
        RagRequest(
            question="Quelle est la definition de la tracabilite ?",
            site_sub_subdomain="contacts",
        )
    )

    assert filters.site_sub_subdomain == "contacts"


def _service() -> RagService:
    retrieval_config = RetrievalConfig(
        vertical="regulation",
        domain="reglementation_transversale",
        subdomain="securite_sanitaire",
        top_k_initial=30,
        top_k_reranked=8,
        min_retrieval_score=0.45,
        min_rerank_score=0.2,
        query_routing_rules=[
            QueryRoutingRule(
                keywords=["definition", "glossaire"],
                vertical="institutionnel",
                domain="onssa",
                subdomain="presentation",
                site_sub_subdomain="glossaire",
            )
        ],
    )
    return RagService(
        retriever=None,  # type: ignore[arg-type]
        reranker=None,  # type: ignore[arg-type]
        prompt_builder=None,  # type: ignore[arg-type]
        llm_client=None,  # type: ignore[arg-type]
        citation_builder=None,  # type: ignore[arg-type]
        evidence_policy=EvidencePolicy(retrieval_config),
        rag_config=RagConfig(max_context_chunks=8),
        retrieval_config=retrieval_config,
    )
