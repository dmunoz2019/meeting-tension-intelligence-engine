from meeting_intelligence.engine import MeetingIntelligenceEngine


def test_engine_marks_example_as_hypothetical() -> None:
    text = "(0:00 - 0:20) Por ejemplo, el sistema no permite esa operación. Es solo un ejemplo."
    payload = MeetingIntelligenceEngine(minimum_tension=0).analyze(text)
    assert payload["records"][0]["certainty"] == "HYPOTHETICAL"


def test_engine_finds_concern() -> None:
    text = "(0:00 - 0:20) Me preocupa que no podamos cubrir todas las sedes."
    payload = MeetingIntelligenceEngine(minimum_tension=0).analyze(text)
    assert payload["records"][0]["act"] == "CONCERN"
    assert payload["records"][0]["dissatisfaction_score"] > 40
