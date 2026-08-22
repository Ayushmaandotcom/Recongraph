import os
from typing import Optional
from recongraph.domain.records import PurchaseRecord, GSTRecord

class DocumentRetriever:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DocumentRetriever, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import PointStruct, VectorParams, Distance
            from sentence_transformers import SentenceTransformer
            
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.client = QdrantClient(":memory:")
            
            # Setup collection
            if not self.client.collection_exists(collection_name="gst_rules"):
                self.client.create_collection(
                    collection_name="gst_rules",
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
            
            # GST laws
            self.laws = [
                {
                    "id": 1,
                    "text": "Section 16(4) of CGST Act: A registered person shall not be entitled to take input tax credit in respect of any invoice or debit note for supply of goods or services or both after the thirtieth day of November following the end of financial year to which such invoice or debit note pertains or furnishing of the relevant annual return, whichever is earlier.",
                    "topic": "date"
                },
                {
                    "id": 2,
                    "text": "Rule 36(4) of CGST Rules: Input tax credit to be availed by a registered person in respect of invoices or debit notes, the details of which have not been furnished by the suppliers under sub-section (1) of section 37 in FORM GSTR-1 or using the invoice furnishing facility, shall not exceed 5 per cent. of the eligible credit available in respect of invoices or debit notes the details of which have been furnished by the suppliers under sub-section (1) of section 37 in FORM GSTR-1 or using the invoice furnishing facility.",
                    "topic": "tax"
                },
                {
                    "id": 3,
                    "text": "Section 16(2) of CGST Act: No registered person shall be entitled to the credit of any input tax in respect of any supply of goods or services or both to him unless he is in possession of a tax invoice or debit note issued by a supplier registered under this Act.",
                    "topic": "default"
                }
            ]
            
            # Index
            points = []
            for law in self.laws:
                vector = self.model.encode(law["text"]).tolist()
                points.append(PointStruct(id=law["id"], vector=vector, payload={"text": law["text"]}))
                
            self.client.upsert(
                collection_name="gst_rules",
                points=points
            )
            self.enabled = True
        except ImportError:
            self.enabled = False

    def retrieve(self, diffs: str) -> str:
        if not getattr(self, "enabled", False):
            # Fallback mock logic if dependencies are missing
            if "Date" in diffs:
                return "Section 16(4) of CGST Act..."
            elif "Tax" in diffs:
                return "Rule 36(4) of CGST Rules..."
            return "Section 16(2) of CGST Act..."
            
        vector = self.model.encode(diffs).tolist()
        hits = self.client.query_points(
            collection_name="gst_rules",
            query=vector,
            limit=1
        ).points
        if hits:
            return hits[0].payload["text"]
        return "No specific rule found."

class LLMExplainer:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                self.client = None
        else:
            self.client = None

    def explain(self, pr: PurchaseRecord, gstr2b: GSTRecord, ml_confidence: float) -> tuple[str, str]:
        # 1. Compute basic differences to feed the LLM context
        inv_diff = pr.reference != gstr2b.reference
        date_diff = pr.record_date != gstr2b.record_date
        tax_diff = pr.amount != gstr2b.amount
        gstin_diff = pr.tax_identity != gstr2b.tax_identity
        
        diff_str = []
        if inv_diff: diff_str.append(f"Invoice differs ('{pr.reference}' vs '{gstr2b.reference}')")
        if date_diff: diff_str.append(f"Date differs ('{pr.record_date}' vs '{gstr2b.record_date}')")
        if tax_diff: diff_str.append(f"Tax amount differs ('{pr.amount}' vs '{gstr2b.amount}')")
        if gstin_diff: diff_str.append(f"GSTIN differs ('{pr.tax_identity}' vs '{gstr2b.tax_identity}')")
        
        diffs = "; ".join(diff_str) if diff_str else "No primary field differences."
        
        # RAG Retrieval
        retriever = DocumentRetriever()
        citation = retriever.retrieve(diffs)
        
        # 2. Fallback logic if no API key is provided
        if not self.client:
            if ml_confidence > 0.90:
                return f"Highly likely match (Confidence: {ml_confidence*100:.1f}%). {diffs} - this appears to be a minor typo or formatting difference.", citation
            elif ml_confidence > 0.75:
                return f"Possible match requiring review (Confidence: {ml_confidence*100:.1f}%). {diffs} - check if this is the same invoice filed with a variation.", citation
            else:
                return f"Unlikely match (Confidence: {ml_confidence*100:.1f}%). {diffs} - these likely represent fundamentally different transactions.", citation

        # 3. Live LLM Call
        prompt = f"""You are a senior Indian GST reconciliation expert. 
Review the following invoice match candidate which failed deterministic matching but was evaluated by our ML model.

Purchase Register Record:
- Invoice: {pr.reference}
- Date: {pr.record_date}
- Amount: {pr.amount}
- GSTIN: {pr.tax_identity}
- Supplier: {pr.vendor_name}

GSTR-2B Record:
- Invoice: {gstr2b.reference}
- Date: {gstr2b.record_date}
- Amount: {gstr2b.amount}
- GSTIN: {gstr2b.tax_identity}
- Supplier: {gstr2b.vendor_name}

Identified Differences: {diffs}
ML Model Calibrated Match Confidence: {ml_confidence*100:.1f}%

<RAG_CONTEXT>
{citation}
</RAG_CONTEXT>

Write exactly 2 sentences explaining why this was flagged for human review and whether it appears to be a genuine match (e.g. an OCR error or timing difference) or a contradiction. You may reference the RAG context if it explains the discrepancy (e.g. claiming ITC within the time limit). Do not output anything else.
"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip(), citation
        except Exception as e:
            return f"Error reaching LLM API: {str(e)}", citation
