class ReconGraphError(Exception):
    """Base exception for all domain errors in ReconGraph."""
    pass

class ConfigurationError(ReconGraphError):
    """Raised when engine configuration is invalid."""
    pass

class EvidenceProviderError(ReconGraphError):
    """Raised when a plugin fails to provide evidence correctly."""
    pass

class EvaluationError(ReconGraphError):
    """Raised when a hypothesis cannot be mathematically evaluated."""
    pass
    
class ReconciliationFallbackError(ReconGraphError):
    """Raised when a catastrophic engine failure occurs requiring human fallback."""
    pass
