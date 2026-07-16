"""BAAI reranker adapter."""

import os
from pathlib import Path
from typing import Any

from onssa_ai.reranking.reranker import Reranker
from onssa_ai.schemas.retrieval import RetrievedChunk


class BgeReranker(Reranker):
    """Lazy local wrapper for BAAI/bge-reranker-v2-m3."""

    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        cache_dir: Path | None = None,
        local_files_only: bool = True,
    ) -> None:
        self.model_name = model_name
        self.device = None if device == "auto" else device
        self.cache_dir = cache_dir
        self.local_files_only = local_files_only
        self._model: Any | None = None

    @property
    def model(self) -> Any:
        if self._model is None:
            if self.cache_dir:
                os.environ.setdefault("HF_HOME", str(self.cache_dir))
                os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(self.cache_dir))
            if self.local_files_only:
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as exc:
                msg = (
                    "Missing ML dependency 'sentence-transformers'. Install the local ML "
                    "extras before reranking: pip install -e .[ml]"
                )
                raise RuntimeError(msg) from exc

            self._model = CrossEncoder(
                self.model_name,
                device=self.device,
                cache_folder=str(self.cache_dir) if self.cache_dir else None,
                trust_remote_code=False,
                automodel_args={"local_files_only": self.local_files_only},
                tokenizer_args={"local_files_only": self.local_files_only},
                config_args={"local_files_only": self.local_files_only},
            )
        return self._model

    def rerank(self, question: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not chunks:
            return []
        pairs = [(question, item.chunk.text) for item in chunks]
        scores = self.model.predict(pairs)
        reranked = [
            item.model_copy(update={"rerank_score": float(score)})
            for item, score in zip(chunks, scores, strict=True)
        ]
        return sorted(reranked, key=lambda item: item.rerank_score or item.score, reverse=True)
