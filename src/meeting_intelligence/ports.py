from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class WordToken:
    text: str
    start_ms: int | None
    end_ms: int | None
    confidence: float | None = None
    speaker_id: str | None = None


@dataclass(frozen=True, slots=True)
class TranscriptSegment:
    text: str
    start_ms: int
    end_ms: int
    confidence: float | None = None
    speaker_id: str | None = None
    words: tuple[WordToken, ...] = ()


@dataclass(frozen=True, slots=True)
class TranscriptArtifact:
    provider: str
    model: str
    language: str | None
    segments: tuple[TranscriptSegment, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SpeakerTurn:
    speaker_id: str
    start_ms: int
    end_ms: int
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class RedactionResult:
    text: str
    entities: tuple[dict[str, Any], ...]


@runtime_checkable
class ASRProvider(Protocol):
    def transcribe(
        self,
        audio_path: Path,
        *,
        language: str | None = None,
    ) -> TranscriptArtifact: ...


@runtime_checkable
class DiarizationProvider(Protocol):
    def diarize(self, audio_path: Path) -> tuple[SpeakerTurn, ...]: ...


@runtime_checkable
class AlignmentProvider(Protocol):
    def align(
        self,
        audio_path: Path,
        transcript: TranscriptArtifact,
    ) -> TranscriptArtifact: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


@runtime_checkable
class Reranker(Protocol):
    def score_pairs(self, query: str, documents: Sequence[str]) -> list[float]: ...


@runtime_checkable
class PIIRedactor(Protocol):
    def redact(self, text: str, *, language: str = "es") -> RedactionResult: ...


@runtime_checkable
class TelemetrySpan(Protocol):
    def __enter__(self) -> TelemetrySpan: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def set_attribute(self, name: str, value: str | int | float | bool) -> None: ...


@runtime_checkable
class TelemetryProvider(Protocol):
    def span(self, name: str) -> TelemetrySpan: ...
