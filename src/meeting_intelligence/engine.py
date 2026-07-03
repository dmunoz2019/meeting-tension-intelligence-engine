from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .adaptive import discover_patterns
from .models import AdaptivePattern, Finding, TranscriptUnit
from .rules import PRODUCTIVE_TEMPLATES
from .sentiment import SentimentResult, analyze_sentiment
from .text import parse_transcript


class MeetingIntelligenceEngine:
    def __init__(self, minimum_tension: float = 16.0) -> None:
        self.minimum_tension = minimum_tension
        self._templates = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in PRODUCTIVE_TEMPLATES.items()
        }

    def discover(self, text: str, limit: int = 80) -> list[AdaptivePattern]:
        return discover_patterns(parse_transcript(text), limit=limit)

    def analyze(self, text: str) -> dict[str, Any]:
        units = parse_transcript(text)
        adaptive_patterns = discover_patterns(units)
        compiled_adaptive = [
            (pattern.pattern_id, re.compile(pattern.python_regex, re.IGNORECASE))
            for pattern in adaptive_patterns
        ]
        findings: list[Finding] = []
        all_records: list[dict[str, Any]] = []

        for index, unit in enumerate(units):
            sentiment = analyze_sentiment(unit.text)
            template_hits = [
                name for name, pattern in self._templates.items() if pattern.search(unit.normalized)
            ]
            adaptive_hits = [
                pattern_id for pattern_id, pattern in compiled_adaptive if pattern.search(unit.normalized)
            ]
            act = self._act(unit, sentiment, template_hits)
            dimensions = self._dimensions(unit, sentiment, template_hits, adaptive_hits)
            risk = self._risk_score(dimensions, sentiment)
            dissatisfaction = self._dissatisfaction_score(sentiment, dimensions)
            tension = round(min(100.0, 0.56 * dissatisfaction + 0.44 * risk), 1)
            level = self._level(tension)
            certainty = (
                "HYPOTHETICAL" if sentiment.hypothetical else "TENTATIVE" if sentiment.hedged else "ASSERTED"
            )
            sentiment_label = self._sentiment_label(sentiment, dissatisfaction)
            context = self._context(units, index)
            record = {
                **unit.to_dict(),
                "act": act,
                "sentiment": sentiment_label,
                "dissatisfaction_score": dissatisfaction,
                "project_risk_score": risk,
                "tension_score": tension,
                "tension_level": level,
                "certainty": certainty,
                "direct_concern": sentiment.direct_concern,
                "reported_concern": sentiment.reported_concern,
                "hypothetical": sentiment.hypothetical,
                "hedged": sentiment.hedged,
                "adaptive_pattern_ids": adaptive_hits,
                "template_hits": template_hits,
                "dimensions": dimensions,
                "context": context,
            }
            all_records.append(record)
            if tension >= self.minimum_tension:
                findings.append(
                    Finding(
                        unit_id=unit.unit_id,
                        start=unit.start,
                        end=unit.end,
                        sentence=unit.text,
                        act=act,
                        sentiment=sentiment_label,
                        dissatisfaction_score=dissatisfaction,
                        project_risk_score=risk,
                        tension_score=tension,
                        tension_level=level,
                        certainty=certainty,
                        review_required=(
                            tension >= 28
                            or act in {"AGREEMENT_CANDIDATE", "SYSTEM_LIMITATION", "SCOPE_EXCLUSION"}
                        ),
                        direct_concern=sentiment.direct_concern,
                        reported_concern=sentiment.reported_concern,
                        hypothetical=sentiment.hypothetical,
                        hedged=sentiment.hedged,
                        adaptive_pattern_ids=adaptive_hits,
                        dimensions=dimensions,
                        context=context,
                    )
                )

        findings.sort(key=lambda item: item.tension_score, reverse=True)
        return {
            "summary": {
                "units": len(units),
                "adaptive_patterns": len(adaptive_patterns),
                "findings": len(findings),
                "high_or_critical": sum(
                    finding.tension_level in {"HIGH", "CRITICAL"} for finding in findings
                ),
            },
            "adaptive_patterns": [pattern.to_dict() for pattern in adaptive_patterns],
            "findings": [finding.to_dict() for finding in findings],
            "records": all_records,
        }

    def analyze_file(self, path: str | Path) -> dict[str, Any]:
        source = Path(path)
        return self.analyze(source.read_text(encoding="utf-8"))

    @staticmethod
    def save_json(payload: dict[str, Any], path: str | Path) -> None:
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _act(
        self,
        unit: TranscriptUnit,
        sentiment: SentimentResult,
        template_hits: list[str],
    ) -> str:
        text = unit.normalized
        if sentiment.hypothetical:
            return "EXAMPLE_HYPOTHETICAL"
        if "AGREEMENT" in template_hits:
            return "AGREEMENT_CANDIDATE"
        if "COMMITMENT" in template_hits:
            return "COMMITMENT"
        if "SYSTEM_LIMITATION" in template_hits:
            return "SYSTEM_LIMITATION"
        if "SCOPE_EXCLUSION" in template_hits:
            return "SCOPE_EXCLUSION"
        if sentiment.direct_concern:
            return "CONCERN"
        if sentiment.reported_concern:
            return "ACKNOWLEDGES_REPORTED_CONCERN"
        if "CLARIFICATION_PRESSURE" in template_hits or text.startswith("¿") or text.endswith("?"):
            return "QUESTION_OR_CHALLENGE"
        if re.search(r"\b(?:necesitamos|debe\w*|tiene\w* que|es necesario)\b", text):
            return "REQUIREMENT_OR_OBLIGATION"
        if re.search(r"\b(?:no estoy de acuerdo|no es aceptable|rechazamos)\b", text):
            return "REJECTION"
        if sentiment.negative_raw >= 3:
            return "WARNING_OR_RISK"
        if sentiment.positive_raw >= 2:
            return "ALIGNMENT"
        return "EXPLANATION"

    @staticmethod
    def _dimensions(
        unit: TranscriptUnit,
        sentiment: SentimentResult,
        template_hits: list[str],
        adaptive_hits: list[str],
    ) -> dict[str, float]:
        dimensions = {
            "emotion": min(100.0, sentiment.dissatisfaction),
            "scope": 0.0,
            "coverage": 0.0,
            "system_gap": 0.0,
            "methodology": 0.0,
            "urgency": 0.0,
            "escalation": 0.0,
            "alignment": min(100.0, sentiment.satisfaction),
        }
        joined = " ".join(template_hits)
        if "SCOPE_EXCLUSION" in joined:
            dimensions["scope"] = 85.0
        if "OMISSION_RESULT" in joined or "NO_MODAL_VERB" in joined:
            dimensions["coverage"] = 62.0
        if "SYSTEM_LIMITATION" in joined:
            dimensions["system_gap"] = 82.0
        if "CLARIFICATION_PRESSURE" in joined:
            dimensions["methodology"] = 58.0
        if "TIME_PRESSURE" in joined:
            dimensions["urgency"] = 70.0
        if "VENDOR_ESCALATION" in joined:
            dimensions["escalation"] = 90.0
        if adaptive_hits:
            dimensions["coverage"] = max(dimensions["coverage"], min(50.0, 8.0 * len(adaptive_hits)))
        if sentiment.hypothetical:
            for key in ("scope", "coverage", "system_gap", "escalation"):
                dimensions[key] *= 0.65
        return {key: round(value, 1) for key, value in dimensions.items()}

    @staticmethod
    def _risk_score(dimensions: dict[str, float], sentiment: SentimentResult) -> float:
        risk = (
            dimensions["scope"] * 0.20
            + dimensions["coverage"] * 0.20
            + dimensions["system_gap"] * 0.18
            + dimensions["methodology"] * 0.12
            + dimensions["urgency"] * 0.12
            + dimensions["escalation"] * 0.18
        )
        if sentiment.hypothetical:
            risk *= 0.72
        return round(min(100.0, risk), 1)

    @staticmethod
    def _dissatisfaction_score(
        sentiment: SentimentResult,
        dimensions: dict[str, float],
    ) -> float:
        score = (
            sentiment.dissatisfaction * 0.72
            + dimensions["escalation"] * 0.12
            + dimensions["methodology"] * 0.08
            + dimensions["urgency"] * 0.08
            - dimensions["alignment"] * 0.10
        )
        if sentiment.reported_concern and not sentiment.direct_concern:
            score *= 0.55
        return round(max(0.0, min(100.0, score)), 1)

    @staticmethod
    def _level(score: float) -> str:
        if score >= 65:
            return "CRITICAL"
        if score >= 43:
            return "HIGH"
        if score >= 28:
            return "MEDIUM"
        if score >= 16:
            return "LOW"
        return "NONE"

    @staticmethod
    def _sentiment_label(sentiment: SentimentResult, dissatisfaction: float) -> str:
        if dissatisfaction >= 42 and sentiment.satisfaction >= 35:
            return "MIXED"
        if dissatisfaction >= 42:
            return "NEGATIVE"
        if sentiment.satisfaction >= 55:
            return "POSITIVE"
        return "NEUTRAL"

    @staticmethod
    def _context(units: list[TranscriptUnit], index: int, radius: int = 1) -> str:
        return " | ".join(
            units[position].text
            for position in range(max(0, index - radius), min(len(units), index + radius + 1))
        )
