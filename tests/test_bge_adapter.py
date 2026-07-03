from meeting_intelligence.adapters.bge import BGEEmbeddingProvider, BGEReranker


class FakeEmbeddingModel:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    def encode(self, texts: list[str], **kwargs: object):
        return {"dense_vecs": [[float(index), 1.0] for index, _ in enumerate(texts)]}


class FakeRerankerModel:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    def compute_score(self, pairs: list[list[str]], *, normalize: bool):
        assert normalize
        return [0.9 if "primary" in document else 0.1 for _, document in pairs]


def test_bge_embedding_adapter_maps_dense_vectors() -> None:
    provider = BGEEmbeddingProvider(model_factory=FakeEmbeddingModel)
    assert provider.embed(["one", "two"]) == [[0.0, 1.0], [1.0, 1.0]]


def test_bge_reranker_maps_scores() -> None:
    reranker = BGEReranker(model_factory=FakeRerankerModel)
    assert reranker.score_pairs("query", ["primary document", "other document"]) == [0.9, 0.1]
