from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class BinaryMetrics:
    precision: float
    recall: float
    f1: float
    accuracy: float
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int


@dataclass(frozen=True, slots=True)
class RetrievalMetrics:
    recall_at_k: float
    reciprocal_rank: float
    hit: bool


def binary_classification_metrics(
    expected: Sequence[bool], predicted: Sequence[bool]
) -> BinaryMetrics:
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted must have the same length")
    if not expected:
        raise ValueError("at least one example is required")
    tp = sum(target and value for target, value in zip(expected, predicted, strict=True))
    fp = sum(not target and value for target, value in zip(expected, predicted, strict=True))
    tn = sum(
        not target and not value for target, value in zip(expected, predicted, strict=True)
    )
    fn = sum(target and not value for target, value in zip(expected, predicted, strict=True))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return BinaryMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        accuracy=(tp + tn) / len(expected),
        true_positive=tp,
        false_positive=fp,
        true_negative=tn,
        false_negative=fn,
    )


def brier_score(expected: Sequence[bool], probabilities: Sequence[float]) -> float:
    _validate_probabilities(expected, probabilities)
    return sum(
        (probability - float(target)) ** 2
        for target, probability in zip(expected, probabilities, strict=True)
    ) / len(expected)


def expected_calibration_error(
    expected: Sequence[bool], probabilities: Sequence[float], *, bins: int = 10
) -> float:
    _validate_probabilities(expected, probabilities)
    if bins < 1:
        raise ValueError("bins must be positive")
    total = len(expected)
    error = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        members = [
            position
            for position, probability in enumerate(probabilities)
            if lower <= probability < upper or (index == bins - 1 and probability == 1.0)
        ]
        if not members:
            continue
        confidence = sum(probabilities[position] for position in members) / len(members)
        accuracy = sum(float(expected[position]) for position in members) / len(members)
        error += len(members) / total * abs(accuracy - confidence)
    return error


def retrieval_metrics(
    relevant_ids: Iterable[str], ranked_ids: Sequence[str], *, k: int
) -> RetrievalMetrics:
    if k < 1:
        raise ValueError("k must be positive")
    relevant = set(relevant_ids)
    if not relevant:
        raise ValueError("at least one relevant id is required")
    considered = ranked_ids[:k]
    matches = relevant.intersection(considered)
    first_rank = next(
        (index for index, item in enumerate(ranked_ids, start=1) if item in relevant),
        None,
    )
    return RetrievalMetrics(
        recall_at_k=len(matches) / len(relevant),
        reciprocal_rank=1.0 / first_rank if first_rank else 0.0,
        hit=bool(matches),
    )


def evidence_span_iou(
    expected_start: int,
    expected_end: int,
    predicted_start: int,
    predicted_end: int,
) -> float:
    if expected_end < expected_start or predicted_end < predicted_start:
        raise ValueError("span end must not precede start")
    intersection = max(
        0,
        min(expected_end, predicted_end) - max(expected_start, predicted_start),
    )
    union = max(expected_end, predicted_end) - min(expected_start, predicted_start)
    if union == 0:
        return 1.0
    return intersection / union


def _validate_probabilities(
    expected: Sequence[bool], probabilities: Sequence[float]
) -> None:
    if len(expected) != len(probabilities):
        raise ValueError("expected and probabilities must have the same length")
    if not expected:
        raise ValueError("at least one example is required")
    if any(not isfinite(value) or value < 0.0 or value > 1.0 for value in probabilities):
        raise ValueError("probabilities must be finite and between zero and one")
