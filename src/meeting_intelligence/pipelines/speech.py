from __future__ import annotations

from contextlib import nullcontext
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..domain import stable_domain_id
from ..ports import (
    AlignmentProvider,
    ASRProvider,
    DiarizationProvider,
    PIIRedactor,
    SpeakerTurn,
    TelemetryProvider,
    TranscriptSegment,
    WordToken,
)


@dataclass(frozen=True, slots=True)
class TimelineUtterance:
    utterance_id: str
    text: str
    start_ms: int
    end_ms: int
    speaker_id: str | None
    confidence: float | None
    words: tuple[WordToken, ...] = ()
    redacted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CanonicalTimeline:
    audio_uri: str
    language: str | None
    provider_chain: tuple[str, ...]
    utterances: tuple[TimelineUtterance, ...]
    speaker_turns: tuple[SpeakerTurn, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CanonicalSpeechPipeline:
    """Build a canonical meeting timeline from pluggable speech components."""

    def __init__(
        self,
        *,
        asr: ASRProvider,
        diarizer: DiarizationProvider | None = None,
        aligner: AlignmentProvider | None = None,
        pii_redactor: PIIRedactor | None = None,
        telemetry: TelemetryProvider | None = None,
    ) -> None:
        self.asr = asr
        self.diarizer = diarizer
        self.aligner = aligner
        self.pii_redactor = pii_redactor
        self.telemetry = telemetry

    def build(
        self,
        audio_path: Path,
        *,
        language: str | None = None,
        redact_pii: bool = True,
    ) -> CanonicalTimeline:
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        span_context = self.telemetry.span("meeting.speech_pipeline") if self.telemetry else nullcontext()
        with span_context as telemetry_span:
            artifact = self.asr.transcribe(audio_path, language=language)
            provider_chain = [artifact.provider]
            if self.aligner is not None:
                artifact = self.aligner.align(audio_path, artifact)
                provider_chain.append(type(self.aligner).__name__)
            turns: tuple[SpeakerTurn, ...] = ()
            if self.diarizer is not None:
                turns = self.diarizer.diarize(audio_path)
                provider_chain.append(type(self.diarizer).__name__)
            utterances = tuple(
                self._to_utterance(
                    segment,
                    turns,
                    language=artifact.language or language or "es",
                    redact_pii=redact_pii,
                )
                for segment in artifact.segments
            )
            if self.pii_redactor is not None and redact_pii:
                provider_chain.append(type(self.pii_redactor).__name__)
            if telemetry_span is not None and hasattr(telemetry_span, "set_attribute"):
                telemetry_span.set_attribute("meeting.audio_uri", str(audio_path))
                telemetry_span.set_attribute("meeting.utterance_count", len(utterances))
                telemetry_span.set_attribute("meeting.speaker_turn_count", len(turns))
                telemetry_span.set_attribute("meeting.language", artifact.language or "unknown")
            return CanonicalTimeline(
                audio_uri=str(audio_path),
                language=artifact.language or language,
                provider_chain=tuple(provider_chain),
                utterances=utterances,
                speaker_turns=turns,
                metadata={
                    "asr_model": artifact.model,
                    "asr_metadata": dict(artifact.metadata),
                    "pii_redacted": bool(self.pii_redactor and redact_pii),
                },
            )

    def _to_utterance(
        self,
        segment: TranscriptSegment,
        turns: tuple[SpeakerTurn, ...],
        *,
        language: str,
        redact_pii: bool,
    ) -> TimelineUtterance:
        if segment.end_ms < segment.start_ms:
            raise ValueError("transcript segment end must not precede start")
        speaker_id = segment.speaker_id or _best_speaker(segment.start_ms, segment.end_ms, turns)
        text = segment.text
        redacted = False
        metadata: dict[str, Any] = {}
        if self.pii_redactor is not None and redact_pii:
            result = self.pii_redactor.redact(text, language=language)
            text = result.text
            redacted = bool(result.entities)
            metadata["pii_entities"] = list(result.entities)
        return TimelineUtterance(
            utterance_id=stable_domain_id(
                "UTT", str(segment.start_ms), str(segment.end_ms), speaker_id, text
            ),
            text=text,
            start_ms=segment.start_ms,
            end_ms=segment.end_ms,
            speaker_id=speaker_id,
            confidence=segment.confidence,
            words=segment.words,
            redacted=redacted,
            metadata=metadata,
        )


def _best_speaker(
    start_ms: int,
    end_ms: int,
    turns: tuple[SpeakerTurn, ...],
) -> str | None:
    best_speaker: str | None = None
    best_overlap = 0
    best_confidence = -1.0
    for turn in turns:
        overlap = max(0, min(end_ms, turn.end_ms) - max(start_ms, turn.start_ms))
        confidence = turn.confidence if turn.confidence is not None else 0.0
        if overlap > best_overlap or (
            overlap == best_overlap and overlap > 0 and confidence > best_confidence
        ):
            best_speaker = turn.speaker_id
            best_overlap = overlap
            best_confidence = confidence
    return best_speaker
