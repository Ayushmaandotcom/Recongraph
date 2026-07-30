from dataclasses import dataclass, field
from recongraph.graph.decision import DecisionPolicy
from recongraph.matching.reference_evidence import ReferenceEvidencePolicy
from recongraph.graph.calibration import CalibrationPolicy

@dataclass(frozen=True)
class ReferenceConfig:
    policy: ReferenceEvidencePolicy = field(default_factory=ReferenceEvidencePolicy)

from enum import Enum
from recongraph.matching.scoring import RelationshipPolicy
from recongraph.matching.pair_scorers import PURCHASE_TO_GST_POLICY

class DecisionMode(Enum):
    LEGACY = "LEGACY"
    SHADOW = "SHADOW"
    FUSION = "FUSION"

@dataclass(frozen=True)
class DecisionConfig:
    policy: DecisionPolicy = field(default_factory=DecisionPolicy)
    relationship_policy: RelationshipPolicy = field(default_factory=lambda: PURCHASE_TO_GST_POLICY)
    decision_mode: DecisionMode = DecisionMode.LEGACY
    calibration_policy: CalibrationPolicy = field(default_factory=lambda: CalibrationPolicy({}))
    explanation_template_path: str | None = None

@dataclass(frozen=True)
class ReviewConfig:
    enabled: bool = True

@dataclass(frozen=True)
class ReconGraphConfig:
    reference_config: ReferenceConfig = field(default_factory=ReferenceConfig)
    decision_config: DecisionConfig = field(default_factory=DecisionConfig)
    review_config: ReviewConfig = field(default_factory=ReviewConfig)
