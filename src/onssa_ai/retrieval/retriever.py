"""Retriever interface and placeholder implementation."""

from onssa_ai.schemas.retrieval import RetrievalRequest, RetrievedChunk


class Retriever:
    """Retrieve candidate evidence chunks."""

    def retrieve(self, request: RetrievalRequest) -> list[RetrievedChunk]:
        raise NotImplementedError("Implement Qdrant-backed retrieval.")
