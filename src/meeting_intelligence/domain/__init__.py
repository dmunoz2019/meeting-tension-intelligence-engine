"""Evidence-first domain contracts.

The domain package intentionally has no dependency on a speech, vector, database,
or orchestration vendor. Adapters translate upstream outputs into these contracts.
"""

from .models import (
    ArtifactKind,
    AssertionMode,
    AuthorityLevel,
    Claim,
    EvidenceSpan,
    FindingKind,
    ModelRun,
    RelationType,
    ReviewState,
    SourceArtifact,
    SpeakerIdentity,
    stable_domain_id,
)

__all__ = [
    "ArtifactKind",
    "AssertionMode",
    "AuthorityLevel",
    "Claim",
    "EvidenceSpan",
    "FindingKind",
    "ModelRun",
    "RelationType",
    "ReviewState",
    "SourceArtifact",
    "SpeakerIdentity",
    "stable_domain_id",
]
