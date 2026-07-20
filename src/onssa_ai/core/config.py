"""Validated application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeSettings(BaseSettings):
    """Environment variables used to locate and override runtime settings."""

    model_config = SettingsConfigDict(env_prefix="ONSSA_", env_file=".env", extra="ignore")

    config_dir: Path = Path("configs")
    app_env: str = "dev"
    log_level: str = "INFO"
    qdrant_host: str | None = None
    qdrant_port: int | None = None
    inference_backend: Literal["vllm", "ollama", "groq"] | None = None
    vllm_base_url: str | None = None
    vllm_model: str | None = None
    vllm_api_key: str | None = None
    ollama_base_url: str | None = None
    ollama_model: str | None = None
    groq_base_url: str | None = None
    groq_model: str | None = None
    groq_api_key: str | None = None


class AppConfig(BaseModel):
    name: str = "onssa-ai-service"
    environment: str = "dev"
    api_prefix: str = "/api/v1"
    request_timeout_seconds: int = 120
    cors_origins: list[str] = Field(default_factory=list)


class PathConfig(BaseModel):
    corpus_path: Path
    chunks_dir: Path
    instruction_dataset_dir: Path
    embeddings_dir: Path
    model_dir: Path


class ModelConfig(BaseModel):
    embedding_model: str
    reranker_model: str
    llm_model: str
    inference_backend: Literal["vllm", "ollama", "groq"]
    embedding_device: str = "auto"
    reranker_device: str = "auto"


class InferenceEndpointConfig(BaseModel):
    base_url: str
    model: str
    timeout_seconds: int = 120


class RetrievalConfig(BaseModel):
    vertical: str
    domain: str
    subdomain: str
    top_k_initial: int
    top_k_reranked: int
    min_retrieval_score: float
    min_rerank_score: float
    require_evidence: bool = True


class RagConfig(BaseModel):
    max_context_chunks: int
    refuse_without_evidence: bool = True
    citation_required: bool = True
    max_answer_tokens: int = 1024


class QdrantConfig(BaseModel):
    host: str
    port: int
    https: bool = False
    collection_name: str
    vector_size: int
    distance: Literal["cosine", "dot", "euclid"]
    payload_indexes: list[str] = Field(default_factory=list)


class Settings(BaseModel):
    runtime: RuntimeSettings
    app: AppConfig
    paths: PathConfig
    models: ModelConfig
    vllm: InferenceEndpointConfig
    ollama: InferenceEndpointConfig
    groq: InferenceEndpointConfig
    retrieval: RetrievalConfig
    rag: RagConfig
    qdrant: QdrantConfig


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}
    if not isinstance(loaded, dict):
        msg = f"Expected YAML mapping in {path}"
        raise ValueError(msg)
    return loaded


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and validate all configuration files."""

    runtime = RuntimeSettings()
    config_dir = runtime.config_dir
    app_yaml = _read_yaml(config_dir / "app.yaml")
    models_yaml = _read_yaml(config_dir / "models.yaml")
    retrieval_yaml = _read_yaml(config_dir / "retrieval.yaml")
    qdrant_yaml = _read_yaml(config_dir / "qdrant.yaml")

    qdrant_data = qdrant_yaml.get("qdrant", {})
    if runtime.qdrant_host:
        qdrant_data["host"] = runtime.qdrant_host
    if runtime.qdrant_port:
        qdrant_data["port"] = runtime.qdrant_port

    vllm_data = models_yaml.get("vllm", {})
    ollama_data = models_yaml.get("ollama", {})
    groq_data = models_yaml.get("groq", {})
    models_data = models_yaml.get("models", {})
    if runtime.inference_backend:
        models_data["inference_backend"] = runtime.inference_backend
    if runtime.vllm_base_url:
        vllm_data["base_url"] = runtime.vllm_base_url
    if runtime.vllm_model:
        vllm_data["model"] = runtime.vllm_model
    if runtime.ollama_base_url:
        ollama_data["base_url"] = runtime.ollama_base_url
    if runtime.ollama_model:
        ollama_data["model"] = runtime.ollama_model
    if runtime.groq_base_url:
        groq_data["base_url"] = runtime.groq_base_url
    if runtime.groq_model:
        groq_data["model"] = runtime.groq_model

    return Settings(
        runtime=runtime,
        app=AppConfig(**app_yaml.get("app", {})),
        paths=PathConfig(**app_yaml.get("paths", {})),
        models=ModelConfig(**models_data),
        vllm=InferenceEndpointConfig(**vllm_data),
        ollama=InferenceEndpointConfig(**ollama_data),
        groq=InferenceEndpointConfig(**groq_data),
        retrieval=RetrievalConfig(**retrieval_yaml.get("retrieval", {})),
        rag=RagConfig(**retrieval_yaml.get("rag", {})),
        qdrant=QdrantConfig(**qdrant_data),
    )
