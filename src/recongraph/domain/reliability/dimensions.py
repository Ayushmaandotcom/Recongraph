from enum import Enum

class ExtractionQuality(str, Enum):
    """How was the value physically obtained?"""
    AUTHORITATIVE = "authoritative"
    HIGH = "high"
    DEGRADED = "degraded"
    LOW = "low"
    FAILED = "failed"

class ParserQuality(str, Enum):
    """How was the raw extraction parsed/normalized?"""
    CANONICAL = "canonical"
    NORMALIZED = "normalized"
    FALLBACK = "fallback"
    RECOVERED = "recovered"
    UNPARSED = "unparsed"

class Completeness(str, Enum):
    """Is the observation present, partial, or missing?"""
    PRESENT = "present"
    PARTIAL = "partial"
    ABSENT = "absent"
    NOT_APPLICABLE = "not_applicable"

class VerificationState(str, Enum):
    """Has the observation been independently verified?"""
    VERIFIED = "verified"
    CROSS_REFERENCED = "cross_referenced"
    MANUAL_ENTRY = "manual_entry"
    UNVERIFIED = "unverified"

class ConfidenceProvenance(str, Enum):
    """What produced the quality assessment itself?"""
    ENGINE_REPORTED = "engine_reported"
    POLICY_ASSIGNED = "policy_assigned"
    DERIVED = "derived"
    UNKNOWN = "unknown"
