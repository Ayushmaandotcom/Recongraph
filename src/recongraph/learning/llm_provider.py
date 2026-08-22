import json
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from recongraph.core.telemetry import trace_function

# -----------------------------------------------------------------------------
# Stage 3: Structured Output Schemas
# -----------------------------------------------------------------------------

class Citation(BaseModel):
    document_id: str = Field(..., description="The ID of the retrieved document used as evidence.")
    relevance_score: float = Field(..., description="A score between 0.0 and 1.0 indicating relevance.")

class AnswerClaims(BaseModel):
    claims: List[str] = Field(..., description="Individual factual claims made in the answer.")
    citations: List[Citation] = Field(default_factory=list, description="Citations backing these claims.")

class StructuredResponse(BaseModel):
    answer: str = Field(..., description="The main response to the user's query.")
    abstained: bool = Field(default=False, description="True if the LLM cannot confidently answer based on the context.")
    reason: Optional[str] = Field(None, description="The reason for abstaining, if applicable.")
    confidence_score: float = Field(..., description="Confidence score of the response (0.0 to 1.0).")
    claims_analysis: Optional[AnswerClaims] = Field(None, description="Breakdown of claims and citations.")

T = TypeVar('T', bound=BaseModel)

# -----------------------------------------------------------------------------
# Stage 2: LLM Provider Protocol
# -----------------------------------------------------------------------------

class LLMProvider(Protocol):
    """Protocol defining the interface for LLM operations."""
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        temperature: float = 0.0,
        max_tokens: int = 2048
    ) -> str:
        """Generate a raw string response."""
        ...
        
    def generate_structured(
        self, 
        prompt: str, 
        response_model: Type[T], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.0
    ) -> T:
        """Generate a response constrained to a Pydantic model."""
        ...

class MockLLMProvider:
    """Fallback / testing provider."""
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        temperature: float = 0.0,
        max_tokens: int = 2048
    ) -> str:
        return "This is a mock response from the fallback LLM provider."
        
    def generate_structured(
        self, 
        prompt: str, 
        response_model: Type[T], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.0
    ) -> T:
        if response_model == StructuredResponse:
            return StructuredResponse(
                answer="This is a mock structured response.",
                confidence_score=0.9,
                abstained=False
            ) # type: ignore
        raise NotImplementedError(f"Mock missing for model {response_model.__name__}")

class GeminiProvider:
    """Gemini-based LLM provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-pro"):
        self.model_name = model_name
        # In a real setup, we would initialize the genai client here
        
    @trace_function("gemini_generate")
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        temperature: float = 0.0,
        max_tokens: int = 2048
    ) -> str:
        # TODO: Implement real Gemini call
        return "This is a mock Gemini response. Set real API key to use."
        
    @trace_function("gemini_generate_structured")
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_structured(
        self, 
        prompt: str, 
        response_model: Type[T], 
        system_prompt: Optional[str] = None,
        temperature: float = 0.0
    ) -> T:
        # TODO: Implement real Gemini structured output using response_schema
        if response_model == StructuredResponse:
            return StructuredResponse(
                answer="This is a mock structured Gemini response.",
                confidence_score=0.95,
                abstained=False
            ) # type: ignore
        raise NotImplementedError(f"Mock missing for model {response_model.__name__}")

def get_llm_provider(provider_name: str = "mock", **kwargs) -> LLMProvider:
    """Factory to get the configured LLM provider."""
    if provider_name == "mock":
        return MockLLMProvider()
    elif provider_name == "gemini":
        return GeminiProvider(**kwargs)
    raise ValueError(f"Unknown provider: {provider_name}")
