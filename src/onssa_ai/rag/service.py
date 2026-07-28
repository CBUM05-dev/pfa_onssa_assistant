"""RAG orchestration service."""

import unicodedata
from uuid import uuid4

from onssa_ai.citations.builder import CitationBuilder
from onssa_ai.core.config import RagConfig, RetrievalConfig
from onssa_ai.llm.base import LLMClient
from onssa_ai.prompts.prompt_builder import PromptBuilder
from onssa_ai.rag.evidence_policy import EvidencePolicy
from onssa_ai.reranking.reranker import Reranker
from onssa_ai.retrieval.retriever import Retriever
from onssa_ai.schemas.rag import RagRequest, RagResponse
from onssa_ai.schemas.retrieval import RetrievalFilters, RetrievalRequest


class RagService:
    """Coordinate retrieval, reranking, prompting, generation, and citations."""

    def __init__(
        self,
        retriever: Retriever,
        reranker: Reranker,
        prompt_builder: PromptBuilder,
        llm_client: LLMClient,
        citation_builder: CitationBuilder,
        evidence_policy: EvidencePolicy,
        rag_config: RagConfig,
        retrieval_config: RetrievalConfig,
    ) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.citation_builder = citation_builder
        self.evidence_policy = evidence_policy
        self.rag_config = rag_config
        self.retrieval_config = retrieval_config

    async def answer(self, request: RagRequest) -> RagResponse:
        request_id = str(uuid4())
        filters = self._resolve_filters(request)
        retrieved = self.retriever.retrieve(
            RetrievalRequest(
                question=request.question,
                filters=filters,
                top_k=None,
            )
        )
        if hasattr(self.retriever, "expand_with_references"):
            retrieved = self.retriever.expand_with_references(retrieved)
        reranked = self.reranker.rerank(request.question, retrieved)
        evidence = reranked[: self.rag_config.max_context_chunks]
        if not self.evidence_policy.is_sufficient(evidence):
            return RagResponse(
                answer="Je ne peux pas repondre de maniere fiable avec les elements disponibles.",
                citations=[],
                evidence=evidence,
                confidence="insufficient",
                refused=True,
                request_id=request_id,
            )
        prompt = self.prompt_builder.build(request.question, evidence)
        answer = await self.llm_client.generate(prompt, self.rag_config.max_answer_tokens)
        return RagResponse(
            answer=answer,
            citations=self.citation_builder.build(evidence, question=request.question),
            evidence=evidence,
            confidence="sufficient",
            refused=False,
            request_id=request_id,
        )

    def _resolve_filters(self, request: RagRequest) -> RetrievalFilters:
        routed = self._route_question(request.question)
        return RetrievalFilters(
            vertical=(
                request.filters.vertical
                or request.vertical
                or routed.vertical
                or self.retrieval_config.vertical
            ),
            domain=(
                request.filters.domain
                or request.domain
                or routed.domain
                or self.retrieval_config.domain
            ),
            subdomain=(
                request.filters.subdomain
                or request.subdomain
                or routed.subdomain
                or self.retrieval_config.subdomain
            ),
            site_sub_subdomain=(
                request.filters.site_sub_subdomain
                or request.site_sub_subdomain
                or routed.site_sub_subdomain
            ),
            language=request.filters.language or request.language,
            document_id=request.filters.document_id,
        )

    def _route_question(self, question: str) -> RetrievalFilters:
        normalized_question = self._normalize_for_routing(question)
        for rule in self.retrieval_config.query_routing_rules:
            if any(
                self._normalize_for_routing(keyword) in normalized_question
                for keyword in rule.keywords
            ):
                return RetrievalFilters(
                    vertical=rule.vertical,
                    domain=rule.domain,
                    subdomain=rule.subdomain,
                    site_sub_subdomain=rule.site_sub_subdomain,
                )
        return RetrievalFilters()

    def _normalize_for_routing(self, value: str) -> str:
        without_accents = "".join(
            char
            for char in unicodedata.normalize("NFKD", value)
            if not unicodedata.combining(char)
        )
        return " ".join(without_accents.lower().split())
