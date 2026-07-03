from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class VectorPrediction:
    label_probabilities: dict[str, float]
    available: bool
    reason: str | None = None


class HashedWeakSupervisionClassifier:
    """Optional classifier that stores no human-readable vocabulary.

    The implementation imports scikit-learn lazily. Project-specific fitted weights
    should be stored in a private model pack, not committed to a public repository.
    """

    def __init__(self, feature_count: int = 2**18) -> None:
        self.feature_count = feature_count
        self._vectorizer: Any = None
        self._classifier: Any = None

    def fit(self, texts: list[str], labels: list[str]) -> None:
        if len(texts) != len(labels):
            raise ValueError("texts and labels must have the same length")
        if len(set(labels)) < 2:
            raise ValueError("at least two classes are required")
        try:
            from sklearn.feature_extraction.text import HashingVectorizer
            from sklearn.linear_model import SGDClassifier
        except ImportError as exc:
            raise RuntimeError("Install the nlp extra: pip install -e '.[nlp]'") from exc

        self._vectorizer = HashingVectorizer(
            n_features=self.feature_count,
            alternate_sign=True,
            ngram_range=(1, 3),
            analyzer="word",
            norm="l2",
            lowercase=True,
        )
        matrix = self._vectorizer.transform(texts)
        self._classifier = SGDClassifier(
            loss="log_loss",
            class_weight="balanced",
            random_state=42,
            max_iter=2000,
            tol=1e-4,
        )
        self._classifier.fit(matrix, labels)

    def predict(self, texts: list[str]) -> list[VectorPrediction]:
        if self._vectorizer is None or self._classifier is None:
            return [VectorPrediction({}, False, "classifier is not fitted") for _ in texts]
        matrix = self._vectorizer.transform(texts)
        probabilities = self._classifier.predict_proba(matrix)
        classes = list(self._classifier.classes_)
        return [
            VectorPrediction(
                label_probabilities={
                    label: round(float(probabilities[row, column]), 5)
                    for column, label in enumerate(classes)
                },
                available=True,
            )
            for row in range(len(texts))
        ]
