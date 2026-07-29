from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from recongraph.domain.records import GSTRecord, PurchaseRecord
from recongraph.matching.scoring import (
    RelationshipPolicy,
    RelationshipScore,
    SignalName,
    calculate_relationship_score,
)
from recongraph.matching.reference_evidence import ReferenceEvidenceContext
from recongraph.domain.vendor.context import VendorIdentityContext
from recongraph.plugins.core_providers import (
    VendorEvidenceProvider,
    TaxEvidenceProvider,
    FinancialEvidenceProvider,
    TemporalEvidenceProvider,
    ReferenceEvidenceProvider,
)
from recongraph.plugins.semantic_providers import SemanticEvidenceProvider
from recongraph.plugins.provider_v2 import EvidenceContributionV2

PURCHASE_TO_GST_MAX_DAYS = 7

PURCHASE_TO_GST_POLICY = RelationshipPolicy(
    weights={
        SignalName.ENTITY: 0.20,
        SignalName.REFERENCE: 0.20,
        SignalName.AMOUNT: 0.25,
        SignalName.TEMPORAL: 0.10,
        SignalName.TAX_IDENTITY: 0.25,
    }
)

PURCHASE_TO_GST_POLICY_WITH_SEMANTICS = RelationshipPolicy(
    weights={
        SignalName.ENTITY: 0.20,
        SignalName.REFERENCE: 0.15,
        SignalName.AMOUNT: 0.25,
        SignalName.TEMPORAL: 0.10,
        SignalName.TAX_IDENTITY: 0.20,
        SignalName.SEMANTICS: 0.10,
    }
)

@dataclass(frozen=True)
class PairScoringResult:
    """Represent raw evidence contributions from Providers."""
    contributions: Mapping[str, EvidenceContributionV2[Any]]
    
    @property
    def signals(self) -> dict[str, float | None]:
        return {k: v.score for k, v in self.contributions.items()}


from typing import Any, Iterable
from recongraph.plugins.provider import EvidenceProvider
from recongraph.matching.purchase_gst_semantics import (
    analyze_purchase_gst_semantics, 
    evaluate_purchase_gst_one_to_one_eligibility, 
    OneToOneEligibility
)
from recongraph.domain.reliability import convert_ocr_report_to_envelope, ExtractionQuality

@dataclass(frozen=True)
class ScoredPair:
    score: float
    coverage: float
    is_eligible: bool
    violations: frozenset[str]
    supporting_metadata: dict[str, Any]
    contributions: dict[str, Any]
    signals: dict[str, float | None]
    relationship: RelationshipScore
    assertions: tuple[Any, ...] = ()


def score_purchase_to_gst(
    purchases: list[PurchaseRecord],
    gsts: list[GSTRecord],
    providers: Iterable[EvidenceProvider],
    policy: RelationshipPolicy
) -> ScoredPair:
    signals = {}
    violations: set[str] = set()
    supporting_metadata = {}
    contributions = {}
    all_assertions = []
    
    # 1. Collect ReliabilityEnvelopes
    envelopes = []
    for record in purchases + gsts:
        if env := getattr(record, "reliability_envelope", None):
            envelopes.append(env)
        elif report := getattr(record, "ocr_confidence_report", None):
            envelopes.append(convert_ocr_report_to_envelope(report))
            
    # 2. Evaluate Evidence Providers
    for provider in providers:
        contrib = provider.evaluate(purchases, gsts)
        contributions[contrib.provider_name] = contrib
        signals[contrib.provider_name] = contrib.score
        violations.update(contrib.violations)
        if contrib.metadata:
            supporting_metadata[contrib.provider_name] = contrib.metadata
            if "assertions" in contrib.metadata:
                all_assertions.extend(contrib.metadata["assertions"])
            
    # 3. Apply Attenuation Policy
    if hasattr(policy, "attenuation_policy"):
        quality_order = {
            ExtractionQuality.AUTHORITATIVE: 4,
            ExtractionQuality.HIGH: 3,
            ExtractionQuality.DEGRADED: 2,
            ExtractionQuality.LOW: 1,
            ExtractionQuality.FAILED: 0
        }
        
        fields_to_check = set((r.signal_name, r.field_name) for r in policy.attenuation_policy.rules)
        for signal_name, field_name in fields_to_check:
            sig_val = signals.get(signal_name)
            if sig_val is None:
                continue
                
            lowest_quality = None
            for env in envelopes:
                profile = env.get(field_name)
                if profile:
                    q = profile.extraction_quality
                    if lowest_quality is None or quality_order.get(q, 5) < quality_order.get(lowest_quality, 5):
                        lowest_quality = q
                            
            if lowest_quality is not None:
                weight, new_violations = policy.attenuation_policy.apply(signal_name, lowest_quality)
                signals[signal_name] = sig_val * weight
                violations.update(new_violations)
            
    semantic_findings = analyze_purchase_gst_semantics(signals)
    legacy_eligibility = evaluate_purchase_gst_one_to_one_eligibility(semantic_findings)
    
    is_eligible = legacy_eligibility.status == OneToOneEligibility.ELIGIBLE
    
    relationship = calculate_relationship_score(
        signals=signals, policy=policy
    )
    
    violations.update({str(f.value) for f in semantic_findings})
    
    if "TEMPORAL_MAX_DAYS_EXCEEDED" in violations:
        is_eligible = False

    # Also check provider-emitted violations (e.g. AMOUNT_MULTIPLE from financial pipeline)
    # against the blocking set — they do not come through analyze_purchase_gst_semantics
    # but must still gate eligibility.
    from recongraph.matching.purchase_gst_semantics import (
        ONE_TO_ONE_BLOCKING_FINDINGS, SemanticFinding
    )
    blocking_values = {f.value for f in ONE_TO_ONE_BLOCKING_FINDINGS}
    if any(v in blocking_values for v in violations):
        is_eligible = False
        
    return ScoredPair(
        score=relationship.score if relationship.score is not None else 0.0,
        coverage=relationship.coverage,
        is_eligible=is_eligible,
        violations=frozenset(violations),
        supporting_metadata=supporting_metadata,
        contributions=contributions,
        signals=signals,
        relationship=relationship,
        assertions=tuple(all_assertions)
    )
