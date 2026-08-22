from typing import Dict, Any, Tuple
from recongraph.domain.records import PurchaseRecord, GSTRecord

class LLMExplainer:
    def __init__(self, provider: str = "mock"):
        self.provider = provider
        
    def _extract_evidence(self, pr: PurchaseRecord, gstr2b: GSTRecord, confidence: float) -> Dict[str, Any]:
        """Extracts structured evidence for the LLM prompt."""
        # Simple evidence extraction
        tax_diff = abs(pr.amount - gstr2b.amount) if pr.amount and gstr2b.amount else 0
        date_diff = abs((pr.record_date - gstr2b.record_date).days) if pr.record_date and gstr2b.record_date else 999
        gstin_match = "exact" if pr.tax_identity == gstr2b.tax_identity else "mismatch"
        
        return {
            "ml_confidence": round(confidence, 3),
            "gstin_match": gstin_match,
            "date_difference": date_diff,
            "tax_difference": float(tax_diff),
            "pr_reference": pr.reference,
            "gst_reference": gstr2b.reference
        }
        
    def explain(self, pr: PurchaseRecord, gstr2b: GSTRecord, confidence: float) -> Tuple[str, str]:
        """
        Generates a human-readable explanation based on ML evidence.
        Returns (explanation_text, citation).
        """
        evidence = self._extract_evidence(pr, gstr2b, confidence)
        
        # In a real implementation, this would construct a prompt and call OpenAI/Anthropic/Gemini
        # For Phase 9, we construct a deterministic structured LLM response based on the evidence.
        
        if confidence >= 0.95:
            action = "Auto-Match recommended."
        elif confidence >= 0.70:
            action = "Review recommended."
        else:
            action = "Reject recommended."
            
        reasoning = f"The records likely refer to the same supplier invoice ({evidence['pr_reference']}). "
        
        if evidence['gstin_match'] == "exact":
            reasoning += "The GSTIN is an exact match. "
        else:
            reasoning += "There is a GSTIN mismatch. "
            
        if evidence['tax_difference'] > 0:
            reasoning += f"However, the tax amount differs by ₹{evidence['tax_difference']} "
            
        if evidence['date_difference'] > 0:
            reasoning += f"and there is a {evidence['date_difference']} day date variance. "
            
        if evidence['tax_difference'] > 0 or evidence['date_difference'] > 0:
            reasoning += "Manual verification is recommended to ensure correct claim."
        else:
            reasoning += "No significant variances detected."
            
        explanation = f"{action} {reasoning}"
        citation = "ReconGraph Structured ML Evaluation Trace"
        
        return explanation, citation
