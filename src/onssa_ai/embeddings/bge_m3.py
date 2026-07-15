"""BAAI/bge-m3 embedding adapter."""

import os
from pathlib import Path
from typing import Any

from onssa_ai.embeddings.embedder import Embedder


class BgeM3Embedder(Embedder):
    """Lazy local wrapper for BAAI/bge-m3 dense embeddings."""

    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        cache_dir: Path | None = None,
        local_files_only: bool = True,
        normalize_embeddings: bool = True,
        show_progress_bar: bool = False,
    ) -> None:
        self.model_name = model_name
        self.device = None if device == "auto" else device
        self.cache_dir = cache_dir
        self.local_files_only = local_files_only
        self.normalize_embeddings = normalize_embeddings
        self.show_progress_bar = show_progress_bar
        self._model: Any | None = None

    @property
    def model(self) -> Any:
        """Load the sentence-transformers model only when embeddings are requested."""

        if self._model is None:
            if self.cache_dir:
                os.environ.setdefault("HF_HOME", str(self.cache_dir))
                os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(self.cache_dir))
            if self.local_files_only:
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                msg = (
                    "Missing ML dependency 'sentence-transformers'. Install the local ML "
                    "extras before building embeddings: pip install -e .[ml]"
                )
                raise RuntimeError(msg) from exc

            cache_kwargs = {"cache_dir": str(self.cache_dir)} if self.cache_dir else None
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                trust_remote_code=False,
                local_files_only=self.local_files_only,
                model_kwargs=cache_kwargs,
                processor_kwargs=cache_kwargs,
                config_kwargs=cache_kwargs,
            )
            return self._model
        return self._model
        
    def _model_load_error(self, exc: Exception) -> RuntimeError:
        cache_hint = f" under {self.cache_dir}" if self.cache_dir else ""
        msg = (
            f"Unable to load embedding model {self.model_name!r} in local/offline mode. "
            f"Preload the model cache{cache_hint}, or set local_files_only=false only in a "
            "controlled preparation environment."
        )
        return RuntimeError(msg)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            vectors = self.model.encode(
                texts,
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=self.show_progress_bar,
            )
        except OSError as exc:
            raise self._model_load_error(exc) from exc
        return vectors.astype("float32").tolist()
