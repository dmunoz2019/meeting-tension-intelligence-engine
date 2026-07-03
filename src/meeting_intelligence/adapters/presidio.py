from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..ports import RedactionResult


class PresidioPIIRedactor:
    """Adapter for Presidio Analyzer and Anonymizer.

    Raw text stays in-process. The returned entity metadata is intentionally
    limited to type, offsets, and confidence; it does not duplicate the value.
    """

    def __init__(
        self,
        *,
        analyzer_factory: Callable[[], Any] | None = None,
        anonymizer_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._analyzer_factory = analyzer_factory
        self._anonymizer_factory = anonymizer_factory
        self._analyzer: Any = None
        self._anonymizer: Any = None

    def _clients(self) -> tuple[Any, Any]:
        if self._analyzer is None:
            if self._analyzer_factory is None:
                try:
                    from presidio_analyzer import AnalyzerEngine
                except ImportError as exc:  # pragma: no cover - optional dependency
                    raise RuntimeError(
                        "Install the privacy extra: pip install 'meeting-tension-intelligence[privacy]'"
                    ) from exc
                self._analyzer = AnalyzerEngine()
            else:
                self._analyzer = self._analyzer_factory()
        if self._anonymizer is None:
            if self._anonymizer_factory is None:
                try:
                    from presidio_anonymizer import AnonymizerEngine
                except ImportError as exc:  # pragma: no cover - optional dependency
                    raise RuntimeError(
                        "Install the privacy extra: pip install 'meeting-tension-intelligence[privacy]'"
                    ) from exc
                self._anonymizer = AnonymizerEngine()
            else:
                self._anonymizer = self._anonymizer_factory()
        return self._analyzer, self._anonymizer

    def redact(self, text: str, *, language: str = "es") -> RedactionResult:
        analyzer, anonymizer = self._clients()
        results = analyzer.analyze(text=text, language=language)
        output = anonymizer.anonymize(text=text, analyzer_results=results)
        entities = tuple(
            {
                "entity_type": str(getattr(item, "entity_type", "UNKNOWN")),
                "start": int(getattr(item, "start", 0)),
                "end": int(getattr(item, "end", 0)),
                "score": float(getattr(item, "score", 0.0)),
            }
            for item in results
        )
        return RedactionResult(text=str(output.text), entities=entities)
