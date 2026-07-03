from pathlib import Path

from meeting_intelligence.pipelines import CanonicalSpeechPipeline
from meeting_intelligence.ports import (
    RedactionResult,
    SpeakerTurn,
    TranscriptArtifact,
    TranscriptSegment,
)


class FakeASR:
    def transcribe(self, audio_path: Path, *, language: str | None = None):
        return TranscriptArtifact(
            provider="fake-asr",
            model="fake-model",
            language=language or "es",
            segments=(
                TranscriptSegment("Código confidencial SECRET", 0, 1000),
                TranscriptSegment("El alcance sigue pendiente", 1000, 2200),
            ),
        )


class FakeDiarizer:
    def diarize(self, audio_path: Path):
        return (
            SpeakerTurn("S1", 0, 900, 0.8),
            SpeakerTurn("S2", 900, 2300, 0.9),
        )


class FakeRedactor:
    def redact(self, text: str, *, language: str = "es"):
        if "SECRET" not in text:
            return RedactionResult(text, ())
        return RedactionResult(
            "Código confidencial <REDACTED>",
            ({"entity_type": "SYNTHETIC_SECRET", "start": 20, "end": 26, "score": 0.99},),
        )


def test_pipeline_builds_speaker_attributed_redacted_timeline(tmp_path: Path) -> None:
    audio = tmp_path / "meeting.wav"
    audio.write_bytes(b"synthetic")
    timeline = CanonicalSpeechPipeline(
        asr=FakeASR(),
        diarizer=FakeDiarizer(),
        pii_redactor=FakeRedactor(),
    ).build(audio, language="es")
    assert timeline.utterances[0].speaker_id == "S1"
    assert timeline.utterances[1].speaker_id == "S2"
    assert timeline.utterances[0].redacted
    assert "SECRET" not in timeline.utterances[0].text
    assert timeline.metadata["pii_redacted"] is True


def test_pipeline_keeps_raw_text_only_when_explicitly_requested(tmp_path: Path) -> None:
    audio = tmp_path / "meeting.wav"
    audio.write_bytes(b"synthetic")
    timeline = CanonicalSpeechPipeline(
        asr=FakeASR(),
        pii_redactor=FakeRedactor(),
    ).build(audio, language="es", redact_pii=False)
    assert "SECRET" in timeline.utterances[0].text
    assert not timeline.utterances[0].redacted
