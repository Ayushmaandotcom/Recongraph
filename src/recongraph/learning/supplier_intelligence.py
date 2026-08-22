"""Supplier intelligence layer for the GST Copilot."""

import sqlite3
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class SupplierRiskSnapshot:
    """Structured risk profile for a supplier based on historical reconciliation data."""

    gstin: str
    total_invoices: int = 0
    match_rate: float = 0.0
    mismatch_rate: float = 0.0
    review_rate: float = 0.0
    reject_rate: float = 0.0
    risk_level: str = "UNKNOWN"  # LOW / MEDIUM / HIGH / UNKNOWN
    common_issues: list = None
    note: str = ""

    def __post_init__(self):
        if self.common_issues is None:
            self.common_issues = []

    def to_dict(self) -> dict:
        return asdict(self)


def _classify_risk(match_rate: float, total: int) -> str:
    """Classify supplier risk level based on match rate."""
    if total < 5:
        return "UNKNOWN"  # Insufficient data
    if match_rate >= 0.95:
        return "LOW"
    if match_rate >= 0.80:
        return "MEDIUM"
    return "HIGH"


def get_supplier_risk_snapshot(
    gstin: str, db_path: str = "hitl_feedback.db"
) -> SupplierRiskSnapshot:
    """
    Build a supplier risk snapshot from the HITL feedback database.

    Queries historical reconciliation outcomes for a given GSTIN and
    computes aggregate statistics.
    """
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Check if table exists
        c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback_v2'"
        )
        if not c.fetchone():
            conn.close()
            return SupplierRiskSnapshot(
                gstin=gstin,
                note="No HITL feedback database found.",
                risk_level="UNKNOWN",
            )

        # Count all entries related to this GSTIN
        c.execute(
            """SELECT reviewer_action, COUNT(*) 
               FROM feedback_v2 
               WHERE purchase_record_id LIKE ? OR gst_record_id LIKE ?
               GROUP BY reviewer_action""",
            (f"%{gstin}%", f"%{gstin}%"),
        )
        action_counts = dict(c.fetchall())
        conn.close()

        total = sum(action_counts.values())
        if total == 0:
            return SupplierRiskSnapshot(
                gstin=gstin,
                note="No historical feedback found for this supplier.",
                risk_level="UNKNOWN",
            )

        approve_count = action_counts.get("approve", 0) + action_counts.get("accept", 0)
        reject_count = action_counts.get("reject", 0)
        review_count = action_counts.get("review", 0) + action_counts.get("escalate", 0)
        mismatch_count = reject_count + review_count

        match_rate = approve_count / total if total > 0 else 0.0
        mismatch_rate = mismatch_count / total if total > 0 else 0.0
        review_rate = review_count / total if total > 0 else 0.0
        reject_rate = reject_count / total if total > 0 else 0.0

        # Identify common issues
        issues = []
        if reject_rate > 0.1:
            issues.append("High rejection rate")
        if review_rate > 0.2:
            issues.append("Frequent manual reviews required")
        if mismatch_rate > 0.15:
            issues.append("Recurring reconciliation mismatches")

        risk_level = _classify_risk(match_rate, total)

        return SupplierRiskSnapshot(
            gstin=gstin,
            total_invoices=total,
            match_rate=round(match_rate, 4),
            mismatch_rate=round(mismatch_rate, 4),
            review_rate=round(review_rate, 4),
            reject_rate=round(reject_rate, 4),
            risk_level=risk_level,
            common_issues=issues,
            note=f"Based on {total} HITL feedback entries.",
        )
    except Exception as e:
        return SupplierRiskSnapshot(
            gstin=gstin,
            note=f"Error querying supplier history: {str(e)}",
            risk_level="UNKNOWN",
        )
