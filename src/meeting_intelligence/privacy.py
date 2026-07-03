from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from .ports import PIIRedactor


class PrivacyMode(StrEnum):
    STRICT = "strict"
    BALANCED = "balanced"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class SanitizedText:
    text: str
    source_sha256: str
    redacted: bool
    entities: tuple[dict[str, Any], ...]
    mode: PrivacyMode

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PrivacyGateway:
    """Central privacy boundary before external inference, embeddings, or export."""

    def __init__(
        self,
        redactor: PIIRedactor | None,
        *,
        mode: PrivacyMode = PrivacyMode.STRICT,
        maximum_quote_characters: int = 240,
    ) -> None:
        if maximum_quote_characters < 1:
            raise ValueError("maximum_quote_characters must be positive")
        self.redactor = redactor
        self.mode = mode
        self.maximum_quote_characters = maximum_quote_characters

    def sanitize(
        self,
        text: str,
        *,
        language: str = "es",
        external: bool = False,
    ) -> SanitizedText:
        source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if self.mode is PrivacyMode.DISABLED:
            if external:
                raise RuntimeError("external inference is blocked when privacy mode is disabled")
            return SanitizedText(text, source_hash, False, (), self.mode)
        if self.redactor is None:
            if external or self.mode is PrivacyMode.STRICT:
                raise RuntimeError("a PII redactor is required by the active privacy policy")
            return SanitizedText(text, source_hash, False, (), self.mode)
        result = self.redactor.redact(text, language=language)
        return SanitizedText(
            text=result.text,
            source_sha256=source_hash,
            redacted=bool(result.entities),
            entities=result.entities,
            mode=self.mode,
        )

    def sanitize_batch(
        self,
        texts: list[str],
        *,
        language: str = "es",
        external: bool = False,
    ) -> list[SanitizedText]:
        return [
            self.sanitize(text, language=language, external=external)
            for text in texts
        ]

    def safe_quote(self, text: str) -> str:
        if len(text) <= self.maximum_quote_characters:
            return text
        cutoff = self.maximum_quote_characters - 1
        return text[:cutoff].rstrip() + "…"
