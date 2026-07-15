"""Qdrant collection management."""

from qdrant_client import QdrantClient
from qdrant_client.http import models

from onssa_ai.core.config import QdrantConfig


class QdrantCollectionManager:
    """Create and maintain the regulatory vector collection."""

    def __init__(self, client: QdrantClient, config: QdrantConfig) -> None:
        self.client = client
        self.config = config

    def ensure_collection(self) -> None:
        distance = {
            "cosine": models.Distance.COSINE,
            "dot": models.Distance.DOT,
            "euclid": models.Distance.EUCLID,
        }[self.config.distance]
        if not self.client.collection_exists(self.config.collection_name):
            self.client.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=models.VectorParams(
                    size=self.config.vector_size,
                    distance=distance,
                ),
            )
        for field_name in self.config.payload_indexes:
            self.client.create_payload_index(
                collection_name=self.config.collection_name,
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
