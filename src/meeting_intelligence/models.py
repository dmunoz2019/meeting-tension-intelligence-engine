from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class TranscriptUnit:
    unit_id: int
    block_id: int
    start: str | None
    end: str | None
    text: str
    normalized: str
    speaker: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AdaptivePattern:
    pattern_id: str
    phrase: str
    python_regex: str
    posix_ere: str
    support: int
    background_support: int
    lift: float
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Finding:
    unit_id: int
    start: str | None
    end: str | None
    sentence: str
    act: str
    sentiment: str
    dissatisfaction_score: float
    project_risk_score: float
    tension_score: float
    tension_level: str
    certainty: str
    review_required: bool
    direct_concern: bool = False
    reported_concern: bool = False
    hypothetical: bool = False
    hedged: bool = False
    adaptive_pattern_ids: list[str] = field(default_factory=list)
    dimensions: dict[str, float] = field(default_factory=dict)
    context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
