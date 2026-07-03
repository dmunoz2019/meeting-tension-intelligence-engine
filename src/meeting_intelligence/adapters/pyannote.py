from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..ports import SpeakerTurn


class PyannoteDiarizer:
    """Lazy adapter for pyannote.audio speaker diarization pipelines."""

    def __init__(
        self,
        model: str = "pyannote/speaker-diarization-community-1",
        *,
        token: str | None = None,
        device: str | None = None,
        pipeline_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.model = model
        self.token = token
        self.device = device
        self._pipeline_factory = pipeline_factory
        self._pipeline: Any = None

    def _get_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline
        factory = self._pipeline_factory
        if factory is None:
            try:
                from pyannote.audio import Pipeline
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "Install the diarization extra: pip install 'meeting-tension-intelligence[diarization]'"
                ) from exc
            factory = Pipeline.from_pretrained
        kwargs: dict[str, Any] = {}
        if self.token:
            kwargs["token"] = self.token
        self._pipeline = factory(self.model, **kwargs)
        if self.device and hasattr(self._pipeline, "to"):
            try:
                import torch
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("pyannote device selection requires torch") from exc
            self._pipeline.to(torch.device(self.device))
        return self._pipeline

    def diarize(self, audio_path: Path) -> tuple[SpeakerTurn, ...]:
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        output = self._get_pipeline()(str(audio_path))
        annotation = getattr(output, "speaker_diarization", output)
        turns: list[SpeakerTurn] = []
        for turn, _, speaker in annotation.itertracks(yield_label=True):
            turns.append(
                SpeakerTurn(
                    speaker_id=str(speaker),
                    start_ms=round(float(turn.start) * 1000),
                    end_ms=round(float(turn.end) * 1000),
                )
            )
        return tuple(turns)
