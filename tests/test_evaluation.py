import pytest

from meeting_intelligence.evaluation import (
    binary_classification_metrics,
    brier_score,
    evidence_span_iou,
    expected_calibration_error,
    retrieval_metrics,
)


def test_classification_and_calibration_metrics() -> None:
    metrics = binary_classification_metrics(
        [True, True, False, False],
        [True, False, True, False],
    )
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5
    assert brier_score([True, False], [0.8, 0.2]) == pytest.approx(0.04)
    assert expected_calibration_error([True, False], [0.8, 0.2], bins=2) == pytest.approx(0.2)


def test_retrieval_and_span_metrics() -> None:
    result = retrieval_metrics({"b", "d"}, ["a", "b", "c"], k=3)
    assert result.recall_at_k == 0.5
    assert result.reciprocal_rank == 0.5
    assert evidence_span_iou(0, 10, 5, 15) == pytest.approx(1 / 3)
