"""Embedding interfaces."""

from abc import ABC, abstractmethod


class Embedder(ABC):
    """Text embedding model interface."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return dense vectors for the provided texts."""
        raise NotImplementedError
