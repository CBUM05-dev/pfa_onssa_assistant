"""BAAI reranker adapter placeholder."""

from onssa_ai.reranking.reranker import Reranker
from onssa_ai.schemas.retrieval import RetrievedChunk


class BgeReranker(Reranker):
    def __init__(self, model_name: str, device: str = "auto") -> None:
        self.model_name = model_name
        self.device = device

    def rerank(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        raise NotImplementedError("Install ML dependencies and implement bge reranking.")
