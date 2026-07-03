from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from .models import (
    AuthorityLevel,
    Claim,
    FindingKind,
    RelationType,
    stable_domain_id,
)

_AUTHORITY_RANK = {
    AuthorityLevel.UNKNOWN: 0,
    AuthorityLevel.OBSERVER: 1,
    AuthorityLevel.CONTRIBUTOR: 2,
    AuthorityLevel.APPROVER: 3,
    AuthorityLevel.CONTRACTUAL_AUTHORITY: 4,
}


@dataclass(frozen=True, slots=True)
class ClaimRelation:
    relation_id: str
    source_claim_id: str
    target_claim_id: str
    relation_type: RelationType
    confidence: float
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        source_claim_id: str,
        target_claim_id: str,
        relation_type: RelationType,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> ClaimRelation:
        if source_claim_id == target_claim_id:
            raise ValueError("a claim cannot relate to itself")
        bounded = max(0.0, min(1.0, confidence))
        return cls(
            relation_id=stable_domain_id(
                "REL", source_claim_id, target_claim_id, relation_type.value
            ),
            source_claim_id=source_claim_id,
            target_claim_id=target_claim_id,
            relation_type=relation_type,
            confidence=bounded,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AuthorityAssessment:
    eligible: bool
    required_authority: AuthorityLevel
    actual_authority: AuthorityLevel
    reasons: tuple[str, ...]
    requires_human_review: bool


class ProjectMemory:
    """In-memory reference implementation of temporal project claim memory."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        self._claims: dict[str, Claim] = {}
        self._relations: dict[str, ClaimRelation] = {}

    @property
    def claims(self) -> tuple[Claim, ...]:
        return tuple(self._claims.values())

    @property
    def relations(self) -> tuple[ClaimRelation, ...]:
        return tuple(self._relations.values())

    def add_claim(self, claim: Claim) -> Claim:
        if claim.project_id != self.project_id:
            raise ValueError("claim belongs to a different project")
        existing = self._claims.get(claim.claim_id)
        if existing is not None and existing != claim:
            raise ValueError("claim id collision with different content")
        self._claims[claim.claim_id] = claim
        return claim

    def relate(
        self,
        source_claim_id: str,
        target_claim_id: str,
        relation_type: RelationType,
        *,
        confidence: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> ClaimRelation:
        self._require_claim(source_claim_id)
        self._require_claim(target_claim_id)
        relation = ClaimRelation.build(
            source_claim_id=source_claim_id,
            target_claim_id=target_claim_id,
            relation_type=relation_type,
            confidence=confidence,
            metadata=metadata,
        )
        self._relations[relation.relation_id] = relation
        return relation

    def supersede(
        self,
        old_claim_id: str,
        new_claim_id: str,
        *,
        confidence: float = 1.0,
    ) -> ClaimRelation:
        return self.relate(
            old_claim_id,
            new_claim_id,
            RelationType.SUPERSEDES,
            confidence=confidence,
        )

    def active_claims(self, *, as_of: datetime | None = None) -> tuple[Claim, ...]:
        moment = as_of or datetime.now(UTC)
        superseded = {
            relation.source_claim_id
            for relation in self._relations.values()
            if relation.relation_type is RelationType.SUPERSEDES
            and self._is_temporally_active(self._claims[relation.target_claim_id], moment)
        }
        return tuple(
            claim
            for claim in self._claims.values()
            if claim.claim_id not in superseded and self._is_temporally_active(claim, moment)
        )

    def related(
        self,
        claim_id: str,
        *,
        relation_type: RelationType | None = None,
        direction: str = "both",
    ) -> tuple[ClaimRelation, ...]:
        self._require_claim(claim_id)
        if direction not in {"incoming", "outgoing", "both"}:
            raise ValueError("direction must be incoming, outgoing, or both")
        output = []
        for relation in self._relations.values():
            if relation_type is not None and relation.relation_type is not relation_type:
                continue
            incoming = relation.target_claim_id == claim_id
            outgoing = relation.source_claim_id == claim_id
            if direction == "incoming" and incoming:
                output.append(relation)
            elif direction == "outgoing" and outgoing:
                output.append(relation)
            elif direction == "both" and (incoming or outgoing):
                output.append(relation)
        return tuple(output)

    def contradictions(self, claim_id: str) -> tuple[Claim, ...]:
        relations = self.related(claim_id, relation_type=RelationType.CONTRADICTS)
        related_ids = {
            relation.target_claim_id
            if relation.source_claim_id == claim_id
            else relation.source_claim_id
            for relation in relations
        }
        return tuple(self._claims[item] for item in related_ids)

    def support_chain(self, claim_id: str, *, maximum_depth: int = 8) -> tuple[str, ...]:
        self._require_claim(claim_id)
        visited: set[str] = set()
        ordered: list[str] = []

        def walk(current: str, depth: int) -> None:
            if depth > maximum_depth or current in visited:
                return
            visited.add(current)
            ordered.append(current)
            for relation in self.related(
                current, relation_type=RelationType.SUPPORTS, direction="incoming"
            ):
                walk(relation.source_claim_id, depth + 1)

        walk(claim_id, 0)
        return tuple(ordered)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "claims": [claim.to_dict() for claim in self.claims],
            "relations": [relation.to_dict() for relation in self.relations],
        }

    def _require_claim(self, claim_id: str) -> Claim:
        try:
            return self._claims[claim_id]
        except KeyError as exc:
            raise KeyError(f"unknown claim: {claim_id}") from exc

    @staticmethod
    def _is_temporally_active(claim: Claim, moment: datetime) -> bool:
        if claim.valid_from is not None and moment < claim.valid_from:
            return False
        return claim.valid_until is None or moment < claim.valid_until


def assess_claim_authority(
    claim: Claim,
    *,
    required_authority: AuthorityLevel = AuthorityLevel.APPROVER,
) -> AuthorityAssessment:
    governed_kinds = {
        FindingKind.AGREEMENT_CANDIDATE,
        FindingKind.DECISION,
        FindingKind.SCOPE_ITEM,
    }
    if claim.kind not in governed_kinds:
        return AuthorityAssessment(
            eligible=True,
            required_authority=AuthorityLevel.UNKNOWN,
            actual_authority=claim.authority,
            reasons=("claim kind does not require approval authority",),
            requires_human_review=False,
        )
    eligible = _AUTHORITY_RANK[claim.authority] >= _AUTHORITY_RANK[required_authority]
    reasons = (
        ("speaker authority satisfies the approval threshold",)
        if eligible
        else ("speaker authority is below the approval threshold",)
    )
    return AuthorityAssessment(
        eligible=eligible,
        required_authority=required_authority,
        actual_authority=claim.authority,
        reasons=reasons,
        requires_human_review=not eligible or claim.confidence < 0.85,
    )
