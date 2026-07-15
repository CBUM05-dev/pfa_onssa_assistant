"""Embedding artifact schemas."""

from pydantic import BaseModel, Field

from onssa_ai.schemas.chunk import ChunkMetadata


class EmbeddedChunk(BaseModel):
    """Chunk plus dense vector ready for Qdrant indexing."""

    chunk_id: str
    text: str = Field(min_length=1)
    metadata: ChunkMetadata
    embedding: list[float]
    embedding_model: str
    embedding_dimension: int
