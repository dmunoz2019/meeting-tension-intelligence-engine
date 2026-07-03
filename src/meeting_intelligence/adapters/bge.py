from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any


class BGEEmbeddingProvider:
    """Lazy FlagEmbedding adapter for multilingual dense retrieval."""

    def __init__(
        self,
        model: str = "BAAI/bge-m3",
        *,
        device: str | None = None,
        batch_size: int = 16,
        max_length: int = 8192,
        model_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.model_name = model
        self.device = device
        self.batch_size = batch_size
        self.max_length = max_length
        self._model_factory = model_factory
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        factory = self._model_factory
        if factory is None:
            try:
                from FlagEmbedding import BGEM3FlagModel
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "Install the BGE extra: pip install 'meeting-tension-intelligence[retrieval-bge]'"
                ) from exc
            factory = BGEM3FlagModel
        kwargs: dict[str, Any] = {"use_fp16": self.device != "cpu"}
        if self.device:
            kwargs["devices"] = self.device
        self._model = factory(self.model_name, **kwargs)
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        output = self._get_model().encode(
            list(texts),
            batch_size=self.batch_size,
            max_length=self.max_length,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        values = output["dense_vecs"] if isinstance(output, dict) else output
        if hasattr(values, "tolist"):
            values = values.tolist()
        return [[float(value) for value in row] for row in values]


class BGEReranker:
    """Lazy FlagEmbedding cross-encoder reranker."""

    def __init__(
        self,
        model: str = "BAAI/bge-reranker-v2-m3",
        *,
        device: str | None = None,
        normalize: bool = True,
        model_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.model_name = model
        self.device = device
        self.normalize = normalize
        self._model_factory = model_factory
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        factory = self._model_factory
        if factory is None:
            try:
                from FlagEmbedding import FlagReranker
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "Install the BGE extra: pip install 'meeting-tension-intelligence[retrieval-bge]'"
                ) from exc
            factory = FlagReranker
        kwargs: dict[str, Any] = {"use_fp16": self.device != "cpu"}
        if self.device:
            kwargs["devices"] = self.device
        self._model = factory(self.model_name, **kwargs)
        return self._model

    def score_pairs(self, query: str, documents: Sequence[str]) -> list[float]:
        if not documents:
            return []
        pairs = [[query, document] for document in documents]
        values = self._get_model().compute_score(pairs, normalize=self.normalize)
        if isinstance(values, (int, float)):
            values = [values]
        if hasattr(values, "tolist"):
            values = values.tolist()
        return [float(value) for value in values]
