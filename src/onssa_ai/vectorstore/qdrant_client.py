"""Qdrant client factory."""

from qdrant_client import QdrantClient

from onssa_ai.core.config import QdrantConfig


def build_qdrant_client(config: QdrantConfig) -> QdrantClient:
    return QdrantClient(host=config.host, port=config.port, https=config.https)
