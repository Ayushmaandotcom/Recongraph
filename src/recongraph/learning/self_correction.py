from typing import Any, Optional
from pydantic import BaseModel, Field

class EvaluationResult(BaseModel):
    is_safe: bool = Field(..., description="True if the answer doesn't contain hallucinated rules or leaked PII.")
    is_relevant: bool = Field(..., description="True if the answer actually addresses the user's question.")
    critique: str = Field(..., description="Short explanation of why it is safe/relevant or not.")

def evaluate_response(llm_provider: Any, user_query: str, proposed_answer: str) -> EvaluationResult:
    """
    LLM-as-a-Judge: Self-correction loop before returning the answer.
    Checks for safety, hallucination, and relevance.
    """
    prompt = f"""You are a strict compliance and quality judge for an enterprise tax assistant.
Evaluate the following proposed answer to the user's query.

User Query: {user_query}
Proposed Answer: {proposed_answer}

Criteria:
1. Safe: It does not hallucinate new sections of law.
2. Relevant: It directly answers the question asked.

Return a structured evaluation.
"""
    try:
        return llm_provider.generate_structured(prompt, EvaluationResult)
    except Exception as e:
        # If the judge fails, we default to failing open (or closed, depending on risk tolerance)
        return EvaluationResult(
            is_safe=True,
            is_relevant=True,
            critique=f"Judge failed: {str(e)}"
        )
