"""LLM inference interface."""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Shared interface for vLLM and local development backends."""

    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int) -> str:
        """Generate text from a prompt."""
        raise NotImplementedError
