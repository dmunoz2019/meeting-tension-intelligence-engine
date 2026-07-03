from meeting_intelligence.sentiment import analyze_sentiment


def test_direct_concern_is_stronger_than_reported_concern() -> None:
    direct = analyze_sentiment("Me preocupa enormemente que el plan falle.")
    reported = analyze_sentiment("Entiendo tu preocupación y revisaremos el plan.")
    assert direct.direct_concern is True
    assert reported.reported_concern is True
    assert direct.dissatisfaction > reported.dissatisfaction


def test_hypothetical_is_detected() -> None:
    result = analyze_sentiment("Por ejemplo, el sistema no podría completar ese paso.")
    assert result.hypothetical is True
