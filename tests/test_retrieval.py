from collections.abc import Sequence

from meeting_intelligence.retrieval import (
    HybridRetriever,
    SearchDocument,
    reciprocal_rank_fusion,
)


class FakeEmbeddings:
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [
            [float("inventario" in text.casefold()), float("alcance" in text.casefold())]
            for text in texts
        ]


class FakeReranker:
    def score_pairs(self, query: str, documents: Sequence[str]) -> list[float]:
        return [1.0 if "inventario" in document.casefold() else 0.1 for document in documents]


def test_rrf_fuses_rankings() -> None:
    fused = reciprocal_rank_fusion(
        [[("a", 10), ("b", 9)], [("b", 1), ("c", 0.5)]],
        k=10,
    )
    assert fused[0][0] == "b"


def test_hybrid_retrieval_uses_lexical_dense_and_reranker() -> None:
    documents = [
        SearchDocument("1", "El inventario negativo debe bloquearse."),
        SearchDocument("2", "El alcance de la primera fase está pendiente."),
        SearchDocument("3", "La agenda social fue aprobada."),
    ]
    retriever = HybridRetriever(
        documents,
        embedding_provider=FakeEmbeddings(),
        reranker=FakeReranker(),
    )
    hits = retriever.search("riesgo de inventario", top_k=2)
    assert hits[0].document_id == "1"
    assert hits[0].reranker_score == 1.0
    assert hits[0].lexical_score > 0
