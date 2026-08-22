import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recongraph.learning.query_router import decompose_complex_query
from recongraph.learning.self_correction import evaluate_response, EvaluationResult
from pydantic import BaseModel

class MockDecompProvider:
    def generate_structured(self, prompt, model_class):
        if "decompose" in prompt.lower():
            class SubQueries(BaseModel):
                queries: list[str]
            return SubQueries(queries=["Fetch invoice data", "Check GST Section 16"])
        else:
            return EvaluationResult(
                is_safe=True,
                is_relevant=True,
                critique="Looks good."
            )

def test_query_decomposition():
    provider = MockDecompProvider()
    queries = decompose_complex_query("Why did invoice INV-123 get rejected under Section 16?", provider)
    
    assert len(queries) == 2
    assert "What is the reconciliation status" in queries[0]

def test_self_correction_judge():
    provider = MockDecompProvider()
    result = evaluate_response(provider, "Can I claim ITC?", "Yes, if you meet Section 16 conditions.")
    
    assert result.is_safe is True
    assert result.is_relevant is True
