from typing import List, Dict, Any, Tuple
from pydantic import BaseModel

from recongraph.learning.llm_provider import AnswerClaims

class GroundingResult(BaseModel):
    is_fully_grounded: bool
    verified_claims: List[str]
    unverified_claims: List[str]
    hallucinated_citations: List[str]

def validate_citations(
    llm_claims: AnswerClaims, 
    retrieved_documents: List[Dict[str, Any]]
) -> GroundingResult:
    """
    Validates that the citations returned by the LLM strictly map to the IDs 
    of the retrieved documents provided in the context.
    
    If the LLM fabricates a citation ID, it is flagged as hallucinated.
    """
    if not llm_claims:
        return GroundingResult(
            is_fully_grounded=True,
            verified_claims=[],
            unverified_claims=[],
            hallucinated_citations=[]
        )

    valid_document_ids = {
        doc.get("metadata", {}).get("document_id")
        for doc in retrieved_documents
        if doc.get("metadata", {}).get("document_id")
    }
    
    verified_claims = []
    unverified_claims = []
    hallucinated_citations = []
    
    for citation in llm_claims.citations:
        if citation.document_id not in valid_document_ids:
            hallucinated_citations.append(citation.document_id)
            
    if hallucinated_citations:
        # If any citation is hallucinated, we consider the whole claim set unverified/risky
        # In a more advanced implementation, we could map citations per-claim.
        unverified_claims.extend(llm_claims.claims)
    else:
        verified_claims.extend(llm_claims.claims)
        
    is_fully_grounded = len(hallucinated_citations) == 0
    
    return GroundingResult(
        is_fully_grounded=is_fully_grounded,
        verified_claims=verified_claims,
        unverified_claims=unverified_claims,
        hallucinated_citations=list(set(hallucinated_citations))
    )
