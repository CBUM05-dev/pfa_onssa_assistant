"""API dependency wiring."""

from functools import lru_cache

from onssa_ai.citations.builder import CitationBuilder
from onssa_ai.core.config import get_settings
from onssa_ai.embeddings.bge_m3 import BgeM3Embedder
from onssa_ai.llm.factory import build_llm_client
from onssa_ai.prompts.prompt_builder import PromptBuilder
from onssa_ai.rag.evidence_policy import EvidencePolicy
from onssa_ai.rag.service import RagService
from onssa_ai.reranking.bge_reranker import BgeReranker
from onssa_ai.retrieval.qdrant_retriever import QdrantRetriever
from onssa_ai.vectorstore.qdrant_client import build_qdrant_client


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    settings = get_settings()
    model_cache_dir = settings.paths.model_dir / "base"
    embedder = BgeM3Embedder(
        model_name=settings.models.embedding_model,
        device=settings.models.embedding_device,
        cache_dir=model_cache_dir,
        local_files_only=True,
    )
    retriever = QdrantRetriever(
        client=build_qdrant_client(settings.qdrant),
        qdrant_config=settings.qdrant,
        retrieval_config=settings.retrieval,
        embedder=embedder,
    )
    reranker = BgeReranker(
        model_name=settings.models.reranker_model,
        device=settings.models.reranker_device,
        cache_dir=model_cache_dir,
        local_files_only=True,
    )
    return RagService(
        retriever=retriever,
        reranker=reranker,
        prompt_builder=PromptBuilder(),
        llm_client=build_llm_client(settings),
        citation_builder=CitationBuilder(),
        evidence_policy=EvidencePolicy(settings.retrieval),
        rag_config=settings.rag,
    )
