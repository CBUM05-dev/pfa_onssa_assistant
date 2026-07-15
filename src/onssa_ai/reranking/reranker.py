"""Reranker interface."""

from onssa_ai.schemas.retrieval import RetrievedChunk


class Reranker:
    """Rerank retrieved chunks against a question."""

    def rerank(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        raise NotImplementedError("Implement BAAI/bge-reranker-v2-m3 reranking.")
