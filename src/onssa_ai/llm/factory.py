"""LLM client factory."""

from onssa_ai.core.config import Settings
from onssa_ai.llm.base import LLMClient
from onssa_ai.llm.groq_client import GroqClient
from onssa_ai.llm.ollama_client import OllamaClient
from onssa_ai.llm.vllm_client import VllmClient


def build_llm_client(settings: Settings) -> LLMClient:
    """Build the configured LLM backend without changing RAG orchestration."""

    backend = settings.models.inference_backend
    if backend == "vllm":
        return VllmClient(
            base_url=settings.vllm.base_url,
            model=settings.vllm.model,
            timeout_seconds=settings.vllm.timeout_seconds,
        )
    if backend == "ollama":
        return OllamaClient(
            base_url=settings.ollama.base_url,
            model=settings.ollama.model,
            timeout_seconds=settings.ollama.timeout_seconds,
        )
    if backend == "groq":
        api_key = settings.runtime.groq_api_key
        if not api_key:
            msg = "ONSSA_GROQ_API_KEY is required when inference_backend is 'groq'."
            raise RuntimeError(msg)
        return GroqClient(
            base_url=settings.groq.base_url,
            model=settings.groq.model,
            timeout_seconds=settings.groq.timeout_seconds,
            api_key=api_key,
        )
    msg = f"Unsupported inference backend: {backend}"
    raise ValueError(msg)
