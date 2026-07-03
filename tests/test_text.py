from meeting_intelligence.text import normalize, parse_transcript


def test_normalize_removes_accents() -> None:
    assert normalize("Preocupación crítica") == "preocupacion critica"


def test_parse_timestamped_transcript() -> None:
    units = parse_transcript("(0:00 - 0:10)\nAna: Me preocupa el plazo.\n\n(0:11 - 0:20)\nLuis: Entiendo.")
    assert len(units) == 2
    assert units[0].speaker == "Ana"
    assert units[0].start == "0:00"
