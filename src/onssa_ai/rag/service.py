"""RAG orchestration service."""

from uuid import uuid4

from onssa_ai.citations.builder import CitationBuilder
from onssa_ai.core.config import RagConfig
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
    ) -> None:
        self.retriever = retriever
        self.reranker = reranker
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.citation_builder = citation_builder
        self.evidence_policy = evidence_policy
        self.rag_config = rag_config

    async def answer(self, request: RagRequest) -> RagResponse:
        request_id = str(uuid4())
        filters = RetrievalFilters(
            vertical=request.vertical,
            domain=request.domain,
            subdomain=request.subdomain,
            language=request.language,
            document_id=request.filters.document_id,
        )
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
            citations=self.citation_builder.build(evidence),
            evidence=evidence,
            confidence="sufficient",
            refused=False,
            request_id=request_id,
        )
