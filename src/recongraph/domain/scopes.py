from enum import Enum
from dataclasses import dataclass
from typing import Optional


class ScopeKind(str, Enum):
    """
    Formal taxonomy of assertion scopes.
    """
    RECORD = "record"
    RECORD_PAIR = "record_pair"
    GROUP = "group"
    GROUP_PAIR = "group_pair"
    HYPOTHESIS = "hypothesis"
    COMPONENT = "component"


@dataclass(frozen=True, order=True)
class SubjectRef:
    """
    A strictly typed, stable identity for a domain subject.
    Does not hold the actual record object, only its stable URN.
    """
    urn: str

    def to_dict(self) -> dict:
        return {"urn": self.urn}


@dataclass(frozen=True)
class PropositionSubject:
    """
    Represents the canonicalized subject arguments for an EvidenceAssertion.
    Retains the claim identity and semantic version to prove it was canonically constructed.
    """
    claim_id: str
    claim_semantic_version: int
    kind: ScopeKind
    left: tuple[SubjectRef, ...]
    right: tuple[SubjectRef, ...]

    def __post_init__(self):
        left_len = len(self.left)
        right_len = len(self.right)

        if left_len == 0 and right_len == 0:
            raise ValueError("SC-001 Violation: Scope cannot be entirely empty.")

        if self.kind == ScopeKind.RECORD:
            if left_len + right_len != 1:
                raise ValueError("SC-002 Violation: RECORD scope must have exactly one subject.")
        elif self.kind == ScopeKind.RECORD_PAIR:
            if left_len != 1 or right_len != 1:
                raise ValueError("SC-002 Violation: RECORD_PAIR must have exactly 1 left and 1 right.")
        elif self.kind == ScopeKind.GROUP_PAIR:
            if left_len == 0 or right_len == 0:
                raise ValueError("SC-002 Violation: GROUP_PAIR must have at least one left and one right.")
            if left_len == 1 and right_len == 1:
                raise ValueError("SC-002 Violation: GROUP_PAIR requires multiple subjects on at least one side.")

        if len(set(self.left)) != left_len:
            raise ValueError("SC-003 Violation: Duplicate subjects in left side.")
        if len(set(self.right)) != right_len:
            raise ValueError("SC-003 Violation: Duplicate subjects in right side.")

    @classmethod
    def create(
        cls,
        claim_descriptor,
        kind: ScopeKind,
        left: frozenset[SubjectRef] | set[SubjectRef] | list[SubjectRef],
        right: Optional[frozenset[SubjectRef] | set[SubjectRef] | list[SubjectRef]] = None
    ) -> 'PropositionSubject':
        if not claim_descriptor.validates_scope_kind(kind):
            raise ValueError(f"SC-008 Violation: Claim {claim_descriptor.claim_id.value} does not allow scope kind {kind.value}.")

        if right is None:
            right = frozenset()

        canon_left = tuple(sorted(left))
        canon_right = tuple(sorted(right))

        if claim_descriptor.symmetry == "symmetric": 
            if canon_right < canon_left:
                canon_left, canon_right = canon_right, canon_left

        return cls(
            claim_id=claim_descriptor.claim_id.value,
            claim_semantic_version=claim_descriptor.semantic_version.value,
            kind=kind,
            left=canon_left,
            right=canon_right
        )

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "claim_semantic_version": self.claim_semantic_version,
            "kind": self.kind.value,
            "left": [s.to_dict() for s in self.left],
            "right": [s.to_dict() for s in self.right]
        }


@dataclass(frozen=True, slots=True)
class Proposition:
    """
    A specific claim applied to a specific subject.
    Mechanically guarantees that the subject was canonically built for this exact claim.
    """
    claim: 'ClaimDescriptor'
    subject: PropositionSubject

    def __post_init__(self):
        if self.subject.claim_id != self.claim.claim_id.value:
            raise ValueError("Proposition construction rejected: claim mismatch.")
        if self.subject.claim_semantic_version != self.claim.semantic_version.value:
            raise ValueError("Proposition construction rejected: claim semantic version mismatch.")

    @classmethod
    def create(cls, claim: 'ClaimDescriptor', kind: ScopeKind, left: frozenset[SubjectRef] | set[SubjectRef] | list[SubjectRef], right: Optional[frozenset[SubjectRef] | set[SubjectRef] | list[SubjectRef]] = None) -> 'Proposition':
        subject = PropositionSubject.create(claim, kind, left, right)
        return cls(claim=claim, subject=subject)
