from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ArtifactKind(StrEnum):
    AUDIO = "audio"
    VIDEO = "video"
    TRANSCRIPT = "transcript"
    DOCUMENT = "document"
    MODEL_OUTPUT = "model_output"


class AssertionMode(StrEnum):
    ASSERTED = "asserted"
    HYPOTHETICAL = "hypothetical"
    QUOTED = "quoted"
    TENTATIVE = "tentative"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class FindingKind(StrEnum):
    CONCERN = "concern"
    DISAGREEMENT = "disagreement"
    REQUIREMENT = "requirement"
    COMMITMENT = "commitment"
    DECISION = "decision"
    AGREEMENT_CANDIDATE = "agreement_candidate"
    SCOPE_ITEM = "scope_item"
    SYSTEM_CAPABILITY = "system_capability"
    SYSTEM_LIMITATION = "system_limitation"
    RISK = "risk"
    QUESTION = "question"
    TEST_CANDIDATE = "test_candidate"


class ReviewState(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    ADJUSTED = "adjusted"


class RelationType(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DUPLICATES = "duplicates"
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"
    RESOLVES = "resolves"
    GENERATES = "generates"
    VALIDATED_BY = "validated_by"
    DERIVED_FROM = "derived_from"


class AuthorityLevel(StrEnum):
    UNKNOWN = "unknown"
    OBSERVER = "observer"
    CONTRIBUTOR = "contributor"
    APPROVER = "approver"
    CONTRACTUAL_AUTHORITY = "contractual_authority"


def stable_domain_id(prefix: str, *parts: object) -> str:
    canonical = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20].upper()
    return f"{prefix}-{digest}"


@dataclass(frozen=True, slots=True)
class SourceArtifact:
    artifact_id: str
    project_id: str
    kind: ArtifactKind
    uri: str
    sha256: str
    media_type: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        project_id: str,
        kind: ArtifactKind,
        uri: str,
        sha256: str,
        media_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SourceArtifact:
        return cls(
            artifact_id=stable_domain_id("ART", project_id, kind.value, uri, sha256),
            project_id=project_id,
            kind=kind,
            uri=uri,
            sha256=sha256,
            media_type=media_type,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SpeakerIdentity:
    speaker_id: str
    display_name: str | None = None
    role: str | None = None
    organization: str | None = None
    authority: AuthorityLevel = AuthorityLevel.UNKNOWN
    confidence: float = 0.0
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvidenceSpan:
    span_id: str
    artifact_id: str
    start_ms: int | None
    end_ms: int | None
    text: str
    checksum: str
    speaker_id: str | None = None
    unit_ids: tuple[int, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        artifact_id: str,
        text: str,
        start_ms: int | None = None,
        end_ms: int | None = None,
        speaker_id: str | None = None,
        unit_ids: tuple[int, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceSpan:
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return cls(
            span_id=stable_domain_id(
                "EV", artifact_id, start_ms, end_ms, speaker_id, checksum
            ),
            artifact_id=artifact_id,
            start_ms=start_ms,
            end_ms=end_ms,
            text=text,
            checksum=checksum,
            speaker_id=speaker_id,
            unit_ids=unit_ids,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ModelRun:
    model_run_id: str
    component: str
    provider: str
    model: str
    version: str | None
    configuration_hash: str
    started_at: datetime
    completed_at: datetime | None = None
    parent_run_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def start(
        cls,
        *,
        component: str,
        provider: str,
        model: str,
        version: str | None,
        configuration: dict[str, Any],
        parent_run_id: str | None = None,
    ) -> ModelRun:
        encoded = json.dumps(configuration, sort_keys=True, default=str).encode("utf-8")
        configuration_hash = hashlib.sha256(encoded).hexdigest()
        started_at = datetime.now(UTC)
        return cls(
            model_run_id=stable_domain_id(
                "RUN", component, provider, model, version, configuration_hash, started_at
            ),
            component=component,
            provider=provider,
            model=model,
            version=version,
            configuration_hash=configuration_hash,
            started_at=started_at,
            parent_run_id=parent_run_id,
        )


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    project_id: str
    meeting_id: str
    kind: FindingKind
    normalized_text: str
    evidence_span_ids: tuple[str, ...]
    assertion_mode: AssertionMode
    confidence: float
    impact: float
    urgency: float
    speaker_id: str | None = None
    authority: AuthorityLevel = AuthorityLevel.UNKNOWN
    review_state: ReviewState = ReviewState.PENDING
    model_run_id: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        project_id: str,
        meeting_id: str,
        kind: FindingKind,
        normalized_text: str,
        evidence_span_ids: tuple[str, ...],
        assertion_mode: AssertionMode = AssertionMode.ASSERTED,
        confidence: float,
        impact: float = 0.0,
        urgency: float = 0.0,
        speaker_id: str | None = None,
        authority: AuthorityLevel = AuthorityLevel.UNKNOWN,
        model_run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Claim:
        bounded_confidence = max(0.0, min(1.0, confidence))
        bounded_impact = max(0.0, min(1.0, impact))
        bounded_urgency = max(0.0, min(1.0, urgency))
        return cls(
            claim_id=stable_domain_id(
                "CLM",
                project_id,
                meeting_id,
                kind.value,
                normalized_text,
                evidence_span_ids,
                assertion_mode.value,
            ),
            project_id=project_id,
            meeting_id=meeting_id,
            kind=kind,
            normalized_text=normalized_text,
            evidence_span_ids=evidence_span_ids,
            assertion_mode=assertion_mode,
            confidence=bounded_confidence,
            impact=bounded_impact,
            urgency=bounded_urgency,
            speaker_id=speaker_id,
            authority=authority,
            model_run_id=model_run_id,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
