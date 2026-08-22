"""Controlled tools for the ReconGraph Copilot.

These functions provide structured, tenant-scoped access to reconciliation
data. The LLM never gets raw database access — only these curated interfaces.
"""

import json
import sqlite3
from typing import Dict, Any, Optional, List


# Reference to the in-memory runs store used by the API
# This will be injected at runtime from main.py
_runs_store: Dict[str, dict] = {}


def set_runs_store(store: Dict[str, dict]):
    """Inject the runs store reference from the API layer."""
    global _runs_store
    _runs_store = store


def get_invoice_details(
    run_id: str, invoice_id: str, tenant_id: str = ""
) -> Dict[str, Any]:
    """Retrieve details for a specific invoice from a reconciliation run."""
    run = _runs_store.get(run_id)
    if not run or run.get("status") != "success":
        return {"error": f"Run {run_id} not found or not completed."}

    result = run.get("result", {})

    # Search auto_matches
    for match in result.get("auto_matches", []):
        hyp = match.get("selected_hypothesis", {})
        for edge in hyp.get("hypothesis_identity", []):
            for urn in edge:
                if invoice_id in urn:
                    return {
                        "found_in": "auto_matches",
                        "decision": "AUTO_MATCH",
                        "hypothesis": hyp,
                        "match_details": match,
                    }

    # Search review_packets
    for pkt in result.get("review_packets", []):
        for p in pkt.get("purchases", []):
            if p.get("record_id") == invoice_id:
                return {
                    "found_in": "review_packets",
                    "packet_id": pkt.get("packet_id", ""),
                    "decision": pkt.get("decision", "REVIEW"),
                    "purchases": pkt.get("purchases", []),
                    "gsts": pkt.get("gsts", []),
                    "champion_probability": pkt.get("champion_probability"),
                    "challenger_probability": pkt.get("challenger_probability"),
                    "llm_explanation": pkt.get("llm_explanation"),
                }
        for g in pkt.get("gsts", []):
            if g.get("record_id") == invoice_id:
                return {
                    "found_in": "review_packets",
                    "packet_id": pkt.get("packet_id", ""),
                    "decision": pkt.get("decision", "REVIEW"),
                    "purchases": pkt.get("purchases", []),
                    "gsts": pkt.get("gsts", []),
                    "champion_probability": pkt.get("champion_probability"),
                    "challenger_probability": pkt.get("challenger_probability"),
                    "llm_explanation": pkt.get("llm_explanation"),
                }

    return {"error": f"Invoice {invoice_id} not found in run {run_id}."}


def get_decision_trace(
    run_id: str, packet_id: str, tenant_id: str = ""
) -> Dict[str, Any]:
    """Retrieve the decision trace for a specific review packet."""
    run = _runs_store.get(run_id)
    if not run or run.get("status") != "success":
        return {"error": f"Run {run_id} not found or not completed."}

    result = run.get("result", {})

    # Search review_packets for matching packet_id
    for pkt in result.get("review_packets", []):
        if pkt.get("packet_id") == packet_id:
            return {
                "packet_id": packet_id,
                "decision": pkt.get("decision", "REVIEW"),
                "polarity": pkt.get("polarity", "NONE"),
                "champion_probability": pkt.get("champion_probability"),
                "challenger_probability": pkt.get("challenger_probability"),
                "llm_explanation": pkt.get("llm_explanation"),
                "llm_citation": pkt.get("llm_citation"),
                "purchases": pkt.get("purchases", []),
                "gsts": pkt.get("gsts", []),
                "missing_evidence": pkt.get("missing_evidence", {}),
                "contradictions": pkt.get("contradictions", []),
                "trajectory": pkt.get("trajectory", []),
            }

    return {"error": f"Packet {packet_id} not found in run {run_id}."}


def get_match_candidates(
    run_id: str, invoice_id: str, tenant_id: str = ""
) -> Dict[str, Any]:
    """Retrieve candidate matches for an invoice."""
    # In a production system this would query the candidate graph
    # For now, derive from the decision trace
    details = get_invoice_details(run_id, invoice_id, tenant_id)
    if "error" in details:
        return details

    return {
        "invoice_id": invoice_id,
        "found_in": details.get("found_in", "unknown"),
        "candidate_count": len(details.get("gsts", [])) + len(details.get("purchases", [])),
        "purchases": details.get("purchases", []),
        "gsts": details.get("gsts", []),
        "decision": details.get("decision", "UNKNOWN"),
    }


def get_supplier_history(
    gstin: str, tenant_id: str = ""
) -> Dict[str, Any]:
    """Query HITL feedback DB for supplier reconciliation history."""
    try:
        conn = sqlite3.connect("hitl_feedback.db")
        c = conn.cursor()

        # Count total feedback entries for this supplier
        c.execute(
            "SELECT COUNT(*) FROM feedback_v2 WHERE purchase_record_id LIKE ? OR gst_record_id LIKE ?",
            (f"%{gstin}%", f"%{gstin}%"),
        )
        total = c.fetchone()[0]

        # Count by action type
        c.execute(
            """SELECT reviewer_action, COUNT(*) 
               FROM feedback_v2 
               WHERE purchase_record_id LIKE ? OR gst_record_id LIKE ?
               GROUP BY reviewer_action""",
            (f"%{gstin}%", f"%{gstin}%"),
        )
        action_counts = dict(c.fetchall())

        conn.close()

        return {
            "gstin": gstin,
            "total_feedback_entries": total,
            "action_breakdown": action_counts,
            "note": "Based on HITL feedback history.",
        }
    except Exception as e:
        return {"gstin": gstin, "error": str(e)}


def get_run_summary(run_id: str, tenant_id: str = "") -> Dict[str, Any]:
    """Get a high-level summary of a reconciliation run."""
    run = _runs_store.get(run_id)
    if not run:
        return {"error": f"Run {run_id} not found."}

    if run.get("status") != "success":
        return {"run_id": run_id, "status": run.get("status"), "message": run.get("message", "")}

    result = run.get("result", {})
    auto_count = len(result.get("auto_matches", []))
    review_count = len(result.get("review_packets", []))
    total = auto_count + review_count

    return {
        "run_id": run_id,
        "status": "success",
        "total_packets": total,
        "auto_matches": auto_count,
        "review_packets": review_count,
        "auto_match_rate": f"{(auto_count / total * 100):.1f}%" if total > 0 else "0%",
        "engine_version": result.get("engine_version", "unknown"),
    }
