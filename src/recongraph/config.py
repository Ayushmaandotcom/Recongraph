from dataclasses import dataclass, field
from recongraph.graph.decision import DecisionPolicy
from recongraph.matching.reference_evidence import ReferenceEvidencePolicy

@dataclass(frozen=True)
class ReferenceConfig:
    policy: ReferenceEvidencePolicy = field(default_factory=ReferenceEvidencePolicy)

from recongraph.matching.scoring import RelationshipPolicy
from recongraph.matching.pair_scorers import PURCHASE_TO_GST_POLICY

@dataclass(frozen=True)
class DecisionConfig:
    policy: DecisionPolicy = field(default_factory=DecisionPolicy)
    relationship_policy: RelationshipPolicy = field(default_factory=lambda: PURCHASE_TO_GST_POLICY)

@dataclass(frozen=True)
class ReviewConfig:
    enabled: bool = True

@dataclass(frozen=True)
class ReconGraphConfig:
    reference_config: ReferenceConfig = field(default_factory=ReferenceConfig)
    decision_config: DecisionConfig = field(default_factory=DecisionConfig)
    review_config: ReviewConfig = field(default_factory=ReviewConfig)
