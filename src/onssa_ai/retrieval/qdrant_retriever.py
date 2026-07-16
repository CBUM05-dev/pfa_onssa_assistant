"""Qdrant-backed vector retriever."""

from typing import Any

from qdrant_client import QdrantClient

from onssa_ai.core.config import QdrantConfig, RetrievalConfig
from onssa_ai.embeddings.embedder import Embedder
from onssa_ai.retrieval.retriever import Retriever
from onssa_ai.schemas.chunk import ChunkMetadata, KnowledgeChunk
from onssa_ai.schemas.retrieval import RetrievalRequest, RetrievedChunk
from onssa_ai.vectorstore.filters import build_payload_filter


class QdrantRetriever(Retriever):
    """Retrieve evidence chunks by vector similarity and metadata filters."""

    def __init__(
        self,
        client: QdrantClient,
        qdrant_config: QdrantConfig,
        retrieval_config: RetrievalConfig,
        embedder: Embedder,
    ) -> None:
        self.client = client
        self.qdrant_config = qdrant_config
        self.retrieval_config = retrieval_config
        self.embedder = embedder

    def retrieve(self, request: RetrievalRequest) -> list[RetrievedChunk]:
        top_k = request.top_k or self.retrieval_config.top_k_initial
        query_vector = self.embedder.embed_texts([request.question])[0]
        response = self.client.query_points(
            collection_name=self.qdrant_config.collection_name,
            query=query_vector,
            query_filter=build_payload_filter(request.filters),
            limit=top_k,
            with_payload=True,
        )
        results = response.points
        return [
            self._to_retrieved_chunk(point.payload or {}, float(point.score))
            for point in results
        ]

    def _to_retrieved_chunk(self, payload: dict[str, Any], score: float) -> RetrievedChunk:
        metadata_fields = set(ChunkMetadata.model_fields)
        metadata_payload = {key: value for key, value in payload.items() if key in metadata_fields}
        chunk = KnowledgeChunk(
            chunk_id=str(payload["chunk_id"]),
            text=str(payload["text"]),
            metadata=ChunkMetadata.model_validate(metadata_payload),
        )
        return RetrievedChunk(chunk=chunk, score=score)
