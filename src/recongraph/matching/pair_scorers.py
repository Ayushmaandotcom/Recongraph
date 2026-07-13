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
    amount_score,
    entity_score,
    reference_score,
    tax_identity_score,
    temporal_score,
)
from recongraph.matching.purchase_gst_semantics import (
    SemanticFinding,
    analyze_purchase_gst_semantics,
)


PURCHASE_TO_GST_MAX_DAYS = 7


PURCHASE_TO_GST_POLICY = RelationshipPolicy(
    weights={
        SignalName.ENTITY: 0.20,
        SignalName.REFERENCE: 0.20,
        SignalName.AMOUNT: 0.25,
        SignalName.TEMPORAL: 0.10,
        SignalName.TAX_IDENTITY: 0.25,
    },
    contradiction_penalties={
        SignalName.TAX_IDENTITY: 0.50,
    },
)


@dataclass(frozen=True)
class PairScoringResult:
    """Represent primitive evidence and its aggregated relationship score."""

    signals: Mapping[SignalName, float | None]
    semantic_findings: tuple[SemanticFinding, ...]
    relationship: RelationshipScore


def score_purchase_to_gst(
    purchase: PurchaseRecord,
    gst_record: GSTRecord,
) -> PairScoringResult:
    """Score compatibility between purchase-side and GST-side evidence."""
    signals = {
        SignalName.ENTITY: entity_score(
            purchase.vendor_name,
            gst_record.vendor_name,
        ),
        SignalName.REFERENCE: reference_score(
            purchase.reference,
            gst_record.reference,
        ),
        SignalName.AMOUNT: amount_score(
            purchase.amount,
            gst_record.amount,
        ),
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

    semantic_findings = analyze_purchase_gst_semantics(signals)

    relationship = calculate_relationship_score(
        signals=signals,
        policy=PURCHASE_TO_GST_POLICY,
    )

    return PairScoringResult(
        signals=signals,
        semantic_findings=semantic_findings,
        relationship=relationship,
    )
