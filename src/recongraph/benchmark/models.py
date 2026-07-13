from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class DatasetMetadata:
    dataset_id: str
    purchase_count: int
    gst_count: int

@dataclass(frozen=True)
class DecisionStatistics:
    auto_match_count: int
    review_ambiguous_count: int
    review_weak_count: int
    no_match_count: int

@dataclass(frozen=True)
class SearchStatistics:
    candidate_edges: int
    components_extracted: int
    max_component_size: int
    avg_component_size: float
    candidate_reduction_ratio: float
    total_hypotheses_evaluated: int

@dataclass(frozen=True)
class EvidenceStatistics:
    signal_distributions: Mapping[str, float]

@dataclass(frozen=True)
class ConfidenceDistribution:
    bins: Mapping[str, int]

@dataclass(frozen=True)
class TimingStatistics:
    total_runtime_ms: float
    candidate_generation_ms: float
    graph_building_ms: float
    search_evaluation_ms: float
    decision_ms: float

@dataclass(frozen=True)
class BenchmarkReport:
    """The fully serializable domain object containing all metric dimensions."""
    dataset_metadata: DatasetMetadata
    decision_statistics: DecisionStatistics
    search_statistics: SearchStatistics
    evidence_statistics: EvidenceStatistics
    confidence_distribution: ConfidenceDistribution
    timing_statistics: TimingStatistics
