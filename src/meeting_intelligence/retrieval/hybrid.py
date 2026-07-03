from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ..ports import EmbeddingProvider, Reranker

_TOKEN_RE = re.compile(r"[\wáéíóúüñ]+", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class SearchDocument:
    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SearchHit:
    document_id: str
    score: float
    text: str
    metadata: dict[str, Any]
    lexical_score: float = 0.0
    dense_score: float = 0.0
    reranker_score: float | None = None


class BM25Index:
    def __init__(
        self,
        documents: Sequence[SearchDocument],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.documents = list(documents)
        self.k1 = k1
        self.b = b
        self._tokens = [_tokens(document.text) for document in self.documents]
        self._frequencies = [Counter(tokens) for tokens in self._tokens]
        self._average_length = (
            sum(len(tokens) for tokens in self._tokens) / len(self._tokens)
            if self._tokens
            else 0.0
        )
        document_frequency: Counter[str] = Counter()
        for tokens in self._tokens:
            document_frequency.update(set(tokens))
        total = len(self.documents)
        self._idf = {
            token: math.log(1.0 + (total - frequency + 0.5) / (frequency + 0.5))
            for token, frequency in document_frequency.items()
        }

    def search(self, query: str, *, limit: int = 50) -> list[tuple[str, float]]:
        query_tokens = _tokens(query)
        scored: list[tuple[str, float]] = []
        for document, frequencies, tokens in zip(
            self.documents, self._frequencies, self._tokens, strict=True
        ):
            score = 0.0
            length = len(tokens)
            for token in query_tokens:
                frequency = frequencies.get(token, 0)
                if frequency == 0:
                    continue
                denominator = frequency + self.k1 * (
                    1.0
                    - self.b
                    + self.b * length / max(self._average_length, 1.0)
                )
                score += self._idf.get(token, 0.0) * frequency * (self.k1 + 1.0) / denominator
            if score > 0:
                scored.append((document.document_id, score))
        scored.sort(key=lambda item: (-item[1], item[0]))
        return scored[: max(1, limit)]


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[tuple[str, float]]],
    *,
    k: int = 60,
    weights: Sequence[float] | None = None,
) -> list[tuple[str, float]]:
    if weights is None:
        weights = [1.0] * len(rankings)
    if len(weights) != len(rankings):
        raise ValueError("weights must match rankings")
    scores: defaultdict[str, float] = defaultdict(float)
    for ranking, weight in zip(rankings, weights, strict=True):
        for rank, (document_id, _) in enumerate(ranking, start=1):
            scores[document_id] += weight / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


class HybridRetriever:
    """BM25 + dense retrieval + RRF + optional cross-encoder reranking."""

    def __init__(
        self,
        documents: Sequence[SearchDocument],
        *,
        embedding_provider: EmbeddingProvider | None = None,
        reranker: Reranker | None = None,
        rrf_k: int = 60,
    ) -> None:
        self.documents = list(documents)
        self._by_id = {document.document_id: document for document in self.documents}
        if len(self._by_id) != len(self.documents):
            raise ValueError("document_id values must be unique")
        self.lexical = BM25Index(self.documents)
        self.embedding_provider = embedding_provider
        self.reranker = reranker
        self.rrf_k = rrf_k
        self._document_embeddings: list[list[float]] | None = None

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        candidate_k: int = 50,
    ) -> list[SearchHit]:
        bounded_candidate_k = max(top_k, candidate_k)
        lexical = self.lexical.search(query, limit=bounded_candidate_k)
        lexical_lookup = dict(lexical)
        rankings: list[list[tuple[str, float]]] = [lexical]
        dense: list[tuple[str, float]] = []
        if self.embedding_provider is not None and self.documents:
            dense = self._dense_search(query, limit=bounded_candidate_k)
            rankings.append(dense)
        dense_lookup = dict(dense)
        fused = reciprocal_rank_fusion(rankings, k=self.rrf_k)
        candidate_ids = [document_id for document_id, _ in fused[:bounded_candidate_k]]
        reranker_scores: dict[str, float] = {}
        if self.reranker is not None and candidate_ids:
            values = self.reranker.score_pairs(
                query,
                [self._by_id[document_id].text for document_id in candidate_ids],
            )
            if len(values) != len(candidate_ids):
                raise ValueError("reranker returned an unexpected number of scores")
            reranker_scores = dict(zip(candidate_ids, values, strict=True))
            candidate_ids.sort(key=lambda value: (-reranker_scores[value], value))
        fused_lookup = dict(fused)
        return [
            SearchHit(
                document_id=document_id,
                score=(
                    reranker_scores[document_id]
                    if reranker_scores
                    else fused_lookup[document_id]
                ),
                text=self._by_id[document_id].text,
                metadata=dict(self._by_id[document_id].metadata),
                lexical_score=lexical_lookup.get(document_id, 0.0),
                dense_score=dense_lookup.get(document_id, 0.0),
                reranker_score=reranker_scores.get(document_id),
            )
            for document_id in candidate_ids[: max(1, top_k)]
        ]

    def _dense_search(self, query: str, *, limit: int) -> list[tuple[str, float]]:
        assert self.embedding_provider is not None
        if self._document_embeddings is None:
            self._document_embeddings = self.embedding_provider.embed(
                [document.text for document in self.documents]
            )
            if len(self._document_embeddings) != len(self.documents):
                raise ValueError("embedding provider returned an unexpected document count")
        query_embeddings = self.embedding_provider.embed([query])
        if len(query_embeddings) != 1:
            raise ValueError("embedding provider must return exactly one query embedding")
        query_vector = query_embeddings[0]
        scored = [
            (document.document_id, _cosine(query_vector, vector))
            for document, vector in zip(
                self.documents, self._document_embeddings, strict=True
            )
        ]
        scored.sort(key=lambda item: (-item[1], item[0]))
        return scored[: max(1, limit)]


def _tokens(text: str) -> list[str]:
    return [token.casefold() for token in _TOKEN_RE.findall(text)]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have equal dimensions")
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
