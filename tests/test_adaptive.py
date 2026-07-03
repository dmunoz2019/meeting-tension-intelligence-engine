from meeting_intelligence.adaptive import discover_patterns
from meeting_intelligence.text import parse_transcript


def test_discovers_repeated_context_phrase() -> None:
    text = """
    (0:00 - 0:10) No podemos cubrir todas las sedes en una sola sesión.
    (0:11 - 0:20) Todas las sedes requieren validación.
    (0:21 - 0:30) El equipo presentó la agenda.
    (0:31 - 0:40) Me preocupa que todas las sedes queden incompletas.
    """
    patterns = discover_patterns(parse_transcript(text), limit=30, minimum_score=0.5)
    phrases = {pattern.phrase for pattern in patterns}
    assert any("sedes" in phrase for phrase in phrases)
