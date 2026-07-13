from dataclasses import dataclass
from enum import Enum, auto
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.graph.decision import DecisionAction
from recongraph.graph.candidate import NodeID

class Difficulty(Enum):
    EASY = auto()
    MEDIUM = auto()
    HARD = auto()
    ADVERSARIAL = auto()

@dataclass(frozen=True)
class ExpectedOutcome:
    """The mathematical ground truth for a synthetic scenario."""
    expected_decision: DecisionAction
    expected_component_urns: frozenset[NodeID]
    expected_hypothesis_edges: frozenset[frozenset[NodeID]]

@dataclass(frozen=True)
class ScenarioSpecification:
    """A declarative recipe for generating a synthetic reconciliation scenario."""
    scenario_id: str
    difficulty: Difficulty
    # Base records before mutations
    base_purchases: tuple[PurchaseRecord, ...]
    base_gsts: tuple[GSTRecord, ...]
    # The mutations to apply to the base records (will be typed in builder/operators)
    purchase_mutations: tuple[tuple[int, object], ...] # (index, operator)
    gst_mutations: tuple[tuple[int, object], ...] # (index, operator)
    expected_outcome: ExpectedOutcome

@dataclass(frozen=True)
class SyntheticDataset:
    """The materialized dataset ready for Benchmarking."""
    dataset_id: str
    purchases: tuple[PurchaseRecord, ...]
    gsts: tuple[GSTRecord, ...]
    expected_outcomes: tuple[ExpectedOutcome, ...]
