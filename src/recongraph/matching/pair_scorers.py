from collections.abc import Mapping
from dataclasses import dataclass

from recongraph.domain.records import GSTRecord, PurchaseRecord
from recongraph.matching.scoring import (
    RelationshipPolicy,
    RelationshipScore,
    SignalName,
    calculate_relationship_score,
)
from recongraph.matching.signals import (
    entity_score,
    tax_identity_score,
    temporal_score,
)
from recongraph.matching.purchase_gst_semantics import (
    SemanticFinding,
    EligibilityResult,
    analyze_purchase_gst_semantics,
    evaluate_purchase_gst_one_to_one_eligibility,
)
from recongraph.matching.reference_evidence import (
    ReferenceEvidenceContext,
    ReferenceEvidenceInterpretation,
    compute_reference_interpretation,
)
from recongraph.domain.financial.pipeline import FinancialEvidencePipeline, AmountInterpretation
from recongraph.domain.financial.amount_projection import project_amount_similarity, ProjectedAmountSimilarity



PURCHASE_TO_GST_MAX_DAYS = 7


PURCHASE_TO_GST_POLICY = RelationshipPolicy(
    weights={
        SignalName.ENTITY: 0.20,
        SignalName.REFERENCE: 0.20,
        SignalName.AMOUNT: 0.25,
        SignalName.TEMPORAL: 0.10,
        SignalName.TAX_IDENTITY: 0.25,
    },
    contradiction_penalties={},
)


@dataclass(frozen=True)
class PairScoringResult:
    """Represent primitive evidence and its aggregated relationship score."""

    signals: Mapping[SignalName, float | None]
    semantic_findings: tuple[SemanticFinding, ...]
    eligibility: EligibilityResult
    relationship: RelationshipScore
    reference_interpretation: ReferenceEvidenceInterpretation
    amount_interpretation: AmountInterpretation
    amount_projection: ProjectedAmountSimilarity


def score_purchase_to_gst(
    purchase: PurchaseRecord,
    gst_record: GSTRecord,
    reference_context: ReferenceEvidenceContext,
) -> PairScoringResult:
    """Score compatibility between purchase-side and GST-side evidence."""
    reference_interpretation = compute_reference_interpretation(
        purchase.reference,
        gst_record.reference,
        reference_context,
    )

    if not purchase.reference or not gst_record.reference:
        ref_signal = None
    else:
        ref_signal = reference_interpretation.score
        
    pipeline = FinancialEvidencePipeline()
    amount_observation = pipeline.extract([purchase], [gst_record])
    amount_interpretation = pipeline.interpret(amount_observation)
    amount_projection = project_amount_similarity(amount_interpretation)

    signals = {
        SignalName.ENTITY: entity_score(
            purchase.vendor_name,
            gst_record.vendor_name,
        ),
        SignalName.REFERENCE: ref_signal,
        SignalName.AMOUNT: amount_projection.similarity,
        SignalName.TEMPORAL: temporal_score(
            purchase.record_date,
            gst_record.record_date,
            max_days=PURCHASE_TO_GST_MAX_DAYS,
        ),
        SignalName.TAX_IDENTITY: tax_identity_score(
            purchase.tax_identity,
            gst_record.tax_identity,
        ),
    }

    semantic_findings = analyze_purchase_gst_semantics(
        signals
    )
    eligibility = evaluate_purchase_gst_one_to_one_eligibility(
        semantic_findings
    )
    relationship = calculate_relationship_score(
        signals=signals,
        policy=PURCHASE_TO_GST_POLICY,
    )

    return PairScoringResult(
        signals=signals,
        semantic_findings=semantic_findings,
        eligibility=eligibility,
        relationship=relationship,
        reference_interpretation=reference_interpretation,
        amount_interpretation=amount_interpretation,
        amount_projection=amount_projection,
    )
