from enum import Enum
from dataclasses import dataclass
from .identity import IdentityDigest, IdentityDomainId


class SemanticDependencyKind(str, Enum):
    CONFIGURATION = "configuration"
    CORPUS_SNAPSHOT = "corpus_snapshot"
    MODEL_ARTIFACT = "model_artifact"
    REGISTRY_SNAPSHOT = "registry_snapshot"
    RULESET = "ruleset"
    OTHER = "other"


class DependencyStability(str, Enum):
    CONTENT_ADDRESSED = "content_addressed"
    IMMUTABLE_VERSION = "immutable_version"
    MUTABLE_REFERENCE = "mutable_reference"


@dataclass(frozen=True, slots=True, order=True)
class SemanticDependencyRef:
    """
    Contextual modifier for a semantic derivation, capable of changing output.
    """
    kind: SemanticDependencyKind
    namespace: IdentityDomainId
    identity: IdentityDigest
    stability: DependencyStability
    semantic_version: str | None = None
