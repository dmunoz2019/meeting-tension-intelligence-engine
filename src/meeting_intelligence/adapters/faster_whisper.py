from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..ports import TranscriptArtifact, TranscriptSegment, WordToken


class FasterWhisperASR:
    """Adapter for SYSTRAN/faster-whisper.

    The model is loaded lazily. Tests may inject ``model_factory`` and therefore
    never download weights.
    """

    def __init__(
        self,
        model: str = "large-v3",
        *,
        device: str = "cpu",
        compute_type: str = "int8",
        beam_size: int = 5,
        vad_filter: bool = True,
        word_timestamps: bool = True,
        model_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.model_name = model
        self.device = device
        self.compute_type = compute_type
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        self.word_timestamps = word_timestamps
        self._model_factory = model_factory
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        factory = self._model_factory
        if factory is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "Install the faster-whisper extra: pip install 'meeting-tension-intelligence[audio-faster-whisper]'"
                ) from exc
            factory = WhisperModel
        self._model = factory(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
        )
        return self._model

    def transcribe(
        self,
        audio_path: Path,
        *,
        language: str | None = None,
    ) -> TranscriptArtifact:
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        model = self._get_model()
        segments_iter, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=self.beam_size,
            vad_filter=self.vad_filter,
            word_timestamps=self.word_timestamps,
        )
        segments: list[TranscriptSegment] = []
        for segment in segments_iter:
            words = tuple(
                WordToken(
                    text=str(getattr(word, "word", "")).strip(),
                    start_ms=_seconds_to_ms(getattr(word, "start", None)),
                    end_ms=_seconds_to_ms(getattr(word, "end", None)),
                    confidence=_optional_float(getattr(word, "probability", None)),
                )
                for word in (getattr(segment, "words", None) or [])
            )
            segments.append(
                TranscriptSegment(
                    text=str(getattr(segment, "text", "")).strip(),
                    start_ms=_seconds_to_ms(getattr(segment, "start", 0.0)) or 0,
                    end_ms=_seconds_to_ms(getattr(segment, "end", 0.0)) or 0,
                    confidence=_optional_float(getattr(segment, "avg_logprob", None)),
                    words=words,
                )
            )
        detected_language = getattr(info, "language", None) or language
        return TranscriptArtifact(
            provider="faster-whisper",
            model=self.model_name,
            language=detected_language,
            segments=tuple(segments),
            metadata={
                "device": self.device,
                "compute_type": self.compute_type,
                "beam_size": self.beam_size,
                "language_probability": _optional_float(
                    getattr(info, "language_probability", None)
                ),
                "duration_seconds": _optional_float(getattr(info, "duration", None)),
            },
        )


def _seconds_to_ms(value: float | int | str | None) -> int | None:
    if value is None:
        return None
    return round(float(value) * 1000)


def _optional_float(value: float | int | str | None) -> float | None:
    if value is None:
        return None
    return float(value)
