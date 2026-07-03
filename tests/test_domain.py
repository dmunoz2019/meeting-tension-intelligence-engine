from datetime import UTC, datetime

from meeting_intelligence.domain import (
    ArtifactKind,
    AssertionMode,
    Claim,
    EvidenceSpan,
    FindingKind,
    ModelRun,
    SourceArtifact,
)


def test_evidence_and_claim_ids_are_stable() -> None:
    artifact = SourceArtifact.build(
        project_id="P1",
        kind=ArtifactKind.TRANSCRIPT,
        uri="private://meeting-1.md",
        sha256="a" * 64,
    )
    first = EvidenceSpan.build(
        artifact_id=artifact.artifact_id,
        text="El calendario no cubre todos los escenarios.",
        start_ms=1000,
        end_ms=3000,
        unit_ids=(4,),
    )
    second = EvidenceSpan.build(
        artifact_id=artifact.artifact_id,
        text="El calendario no cubre todos los escenarios.",
        start_ms=1000,
        end_ms=3000,
        unit_ids=(4,),
    )
    assert first.span_id == second.span_id
    claim = Claim.build(
        project_id="P1",
        meeting_id="M1",
        kind=FindingKind.RISK,
        normalized_text="coverage schedule risk",
        evidence_span_ids=(first.span_id,),
        assertion_mode=AssertionMode.ASSERTED,
        confidence=1.4,
        impact=-1,
        urgency=0.5,
    )
    assert claim.confidence == 1.0
    assert claim.impact == 0.0
    assert claim.urgency == 0.5


def test_model_run_hashes_configuration() -> None:
    run = ModelRun.start(
        component="retrieval",
        provider="local",
        model="bm25-rrf",
        version="1",
        configuration={"rrf_k": 60},
    )
    assert run.started_at.tzinfo == UTC
    assert len(run.configuration_hash) == 64
    assert run.model_run_id.startswith("RUN-")
    assert run.started_at <= datetime.now(UTC)
