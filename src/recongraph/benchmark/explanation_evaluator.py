import pytest
from recongraph.graph.llm_explainer import LLMExplainer
from recongraph.domain.records import PurchaseRecord, GSTRecord
from decimal import Decimal
from datetime import date

class MockAnthropicClient:
    def __init__(self, mock_response=""):
        self.mock_response = mock_response
        
    class Messages:
        def __init__(self, parent):
            self.parent = parent
            
        def create(self, **kwargs):
            class Response:
                class Content:
                    def __init__(self, text):
                        self.text = text
                def __init__(self, text):
                    self.content = [self.Content(text)]
            return Response(self.parent.mock_response)
            
    @property
    def messages(self):
        return self.Messages(self)

def test_explanation_json_parsing():
    explainer = LLMExplainer()
    
    # Mock Anthropic Client with valid JSON
    valid_json = '''
    {
      "explanation": "This is a minor spelling difference in the invoice number. It appears to be a genuine match.",
      "cited_sources": ["Section 16(4) of CGST Act"],
      "genuine_match": true
    }
    '''
    explainer.client = MockAnthropicClient(valid_json)
    
    pr = PurchaseRecord("1", "Vendor A", "INV001", Decimal("100"), date(2023,1,1), "GSTIN1")
    gs = GSTRecord("2", "Vendor A", "INV-001", Decimal("100"), date(2023,1,1), "GSTIN1")
    
    explanation, citation = explainer.explain(pr, gs, 0.95)
    
    assert "**Verified Genuine Match:**" in explanation
    assert "spelling difference" in explanation
    # The citation should not trigger a hallucination warning because "Section 16(4) of CGST Act" is in the default mock retrieval.
    assert "Hallucinated Citation Detected" not in explanation

def test_hallucination_detection():
    explainer = LLMExplainer()
    
    # Mock Anthropic Client with a hallucinated source
    hallucinated_json = '''
    {
      "explanation": "This is a contradiction.",
      "cited_sources": ["Section 99(9) of Fake Tax Law"],
      "genuine_match": false
    }
    '''
    explainer.client = MockAnthropicClient(hallucinated_json)
    
    pr = PurchaseRecord("1", "Vendor A", "INV001", Decimal("100"), date(2023,1,1), "GSTIN1")
    gs = GSTRecord("2", "Vendor A", "INV-001", Decimal("100"), date(2023,1,1), "GSTIN1")
    
    explanation, citation = explainer.explain(pr, gs, 0.95)
    
    assert "**Flagged as Contradiction:**" in explanation
    assert "Hallucinated Citation Detected" in explanation
    assert "Fake Tax Law" in explanation

def test_invalid_json_fallback():
    explainer = LLMExplainer()
    
    invalid_json = "I think this is a match because of the invoice."
    explainer.client = MockAnthropicClient(invalid_json)
    
    pr = PurchaseRecord("1", "Vendor", "INV", Decimal("10"), date(2023,1,1), "GSTIN")
    gs = GSTRecord("2", "Vendor", "INV", Decimal("10"), date(2023,1,1), "GSTIN")
    
    explanation, citation = explainer.explain(pr, gs, 0.9)
    assert "Error: LLM returned invalid JSON" in explanation
