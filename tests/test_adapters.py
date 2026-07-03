from pathlib import Path
from types import SimpleNamespace

from meeting_intelligence.adapters import (
    FasterWhisperASR,
    PresidioPIIRedactor,
    PyannoteDiarizer,
)


class FakeWhisperModel:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args = args
        self.kwargs = kwargs

    def transcribe(self, *args: object, **kwargs: object):
        word = SimpleNamespace(word=" hola", start=0.1, end=0.4, probability=0.9)
        segment = SimpleNamespace(
            text=" Hola mundo",
            start=0.0,
            end=1.0,
            avg_logprob=-0.2,
            words=[word],
        )
        info = SimpleNamespace(language="es", language_probability=0.99, duration=1.0)
        return iter([segment]), info


class FakeAnnotation:
    def itertracks(self, *, yield_label: bool):
        assert yield_label
        turn = SimpleNamespace(start=0.0, end=1.5)
        yield turn, None, "SPEAKER_00"


class FakeDiarizationPipeline:
    def __call__(self, path: str) -> FakeAnnotation:
        assert path
        return FakeAnnotation()


class FakeAnalyzer:
    def analyze(self, *, text: str, language: str):
        assert language == "es"
        return [SimpleNamespace(entity_type="EMAIL_ADDRESS", start=11, end=24, score=0.98)]


class FakeAnonymizer:
    def anonymize(self, *, text: str, analyzer_results: object):
        assert analyzer_results
        return SimpleNamespace(text="Contactar a <EMAIL_ADDRESS>")


def test_faster_whisper_adapter_maps_segments(tmp_path: Path) -> None:
    audio = tmp_path / "meeting.wav"
    audio.write_bytes(b"synthetic")
    adapter = FasterWhisperASR(model_factory=FakeWhisperModel)
    artifact = adapter.transcribe(audio, language="es")
    assert artifact.provider == "faster-whisper"
    assert artifact.language == "es"
    assert artifact.segments[0].end_ms == 1000
    assert artifact.segments[0].words[0].start_ms == 100


def test_pyannote_adapter_maps_turns(tmp_path: Path) -> None:
    audio = tmp_path / "meeting.wav"
    audio.write_bytes(b"synthetic")
    adapter = PyannoteDiarizer(pipeline_factory=lambda *args, **kwargs: FakeDiarizationPipeline())
    turns = adapter.diarize(audio)
    assert turns[0].speaker_id == "SPEAKER_00"
    assert turns[0].end_ms == 1500


def test_presidio_adapter_does_not_echo_entity_value() -> None:
    adapter = PresidioPIIRedactor(
        analyzer_factory=FakeAnalyzer,
        anonymizer_factory=FakeAnonymizer,
    )
    result = adapter.redact("Contactar a a@example.com")
    assert result.text == "Contactar a <EMAIL_ADDRESS>"
    assert result.entities[0]["entity_type"] == "EMAIL_ADDRESS"
    assert "a@example.com" not in str(result.entities)
