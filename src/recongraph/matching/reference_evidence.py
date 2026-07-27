import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping, Optional, Tuple

from recongraph.normalization.text import normalize_reference

@dataclass(frozen=True)
class ReferenceIdentityEvidence:
    normalized_a: str
    normalized_b: str
    exact_normalized_match: bool
    shared_numeric_tokens: tuple[str, ...]

def _extract_numeric_tokens(reference: str) -> tuple[str, ...]:
    return tuple(sorted(set(re.findall(r"\d+", reference))))

def extract_reference_identity(
    reference_a: str | None,
    reference_b: str | None,
) -> ReferenceIdentityEvidence | None:
    if reference_a is None or not reference_a.strip():
        return None
    if reference_b is None or not reference_b.strip():
        return None

    normalized_a = normalize_reference(reference_a)
    normalized_b = normalize_reference(reference_b)

    if not normalized_a or not normalized_b:
        return None

    exact_match = (normalized_a == normalized_b)

    tokens_a = set(_extract_numeric_tokens(reference_a))
    tokens_b = set(_extract_numeric_tokens(reference_b))

    shared_tokens = tuple(sorted(tokens_a & tokens_b))

    return ReferenceIdentityEvidence(
        normalized_a=normalized_a,
        normalized_b=normalized_b,
        exact_normalized_match=exact_match,
        shared_numeric_tokens=shared_tokens,
    )

from collections import Counter
from collections.abc import Iterable, Mapping
from types import MappingProxyType

@dataclass(frozen=True)
class ReferenceCorpusProfile:
    reference_count: int
    normalized_reference_frequency: Mapping[str, int]
    numeric_token_document_frequency: Mapping[str, int]

    def __post_init__(self) -> None:
        if self.reference_count < 0:
            raise ValueError("reference_count must be >= 0")

        sum_freq = 0
        for k, v in self.normalized_reference_frequency.items():
            if not k or k != normalize_reference(k):
                raise ValueError("invalid normalized key")
            if v < 1 or v > self.reference_count:
                raise ValueError("invalid frequency")
            sum_freq += v

        if self.reference_count > 0 and sum_freq != self.reference_count:
            raise ValueError("inconsistent normalized frequency sum")

        for k, v in self.numeric_token_document_frequency.items():
            if not k or not k.isdigit():
                raise ValueError("invalid numeric token")
            if v < 1 or v > self.reference_count:
                raise ValueError("invalid token df")

        object.__setattr__(self, "normalized_reference_frequency", MappingProxyType(dict(self.normalized_reference_frequency)))
        object.__setattr__(self, "numeric_token_document_frequency", MappingProxyType(dict(self.numeric_token_document_frequency)))

def build_reference_corpus_profile(
    references: Iterable[str | None],
) -> ReferenceCorpusProfile:
    reference_count = 0
    norm_freq: Counter[str] = Counter()
    token_df: Counter[str] = Counter()

    for reference in references:
        if reference is None or not reference.strip():
            continue

        normalized = normalize_reference(reference)
        if not normalized:
            continue

        reference_count += 1
        norm_freq[normalized] += 1

        unique_tokens = _extract_numeric_tokens(reference)
        for token in unique_tokens:
            token_df[token] += 1

    return ReferenceCorpusProfile(
        reference_count=reference_count,
        normalized_reference_frequency=norm_freq,
        numeric_token_document_frequency=token_df,
    )

@dataclass(frozen=True)
class NormalizedReferenceStatistics:
    normalized_reference: str
    frequency: int

    def __post_init__(self) -> None:
        if not self.normalized_reference or self.normalized_reference != normalize_reference(self.normalized_reference):
            raise ValueError("invalid normalized reference")
        if self.frequency < 1:
            raise ValueError("frequency must be >= 1")

@dataclass(frozen=True)
class ReferenceTokenStatistics:
    token: str
    document_frequency: int

    def __post_init__(self) -> None:
        if not self.token or not self.token.isdigit():
            raise ValueError("invalid numeric token")
        if self.document_frequency < 1:
            raise ValueError("document_frequency must be >= 1")

@dataclass(frozen=True)
class NormalizedReferenceEvidence:
    normalized_reference: str
    statistics: NormalizedReferenceStatistics | None

    def __post_init__(self) -> None:
        if not self.normalized_reference or self.normalized_reference != normalize_reference(self.normalized_reference):
            raise ValueError("invalid normalized reference")
        if self.statistics is not None and self.statistics.normalized_reference != self.normalized_reference:
            raise ValueError("statistics mismatch")

@dataclass(frozen=True)
class SharedNumericTokenEvidence:
    token: str
    statistics: ReferenceTokenStatistics | None

    def __post_init__(self) -> None:
        if not self.token or not self.token.isdigit():
            raise ValueError("invalid numeric token")
        if self.statistics is not None and self.statistics.token != self.token:
            raise ValueError("statistics mismatch")

@dataclass(frozen=True)
class EnrichedReferenceEvidence:
    identity: ReferenceIdentityEvidence
    reference_count: int
    normalized_references: tuple[NormalizedReferenceEvidence, ...]
    shared_numeric_tokens: tuple[SharedNumericTokenEvidence, ...]

    def __post_init__(self) -> None:
        if self.reference_count < 0:
            raise ValueError("reference_count must be >= 0")

        norm_refs = [e.normalized_reference for e in self.normalized_references]
        if norm_refs != sorted(norm_refs):
            raise ValueError("normalized_references must be sorted")
        if len(norm_refs) != len(set(norm_refs)):
            raise ValueError("normalized_references must not contain duplicates")

        shared_tokens = [e.token for e in self.shared_numeric_tokens]
        if shared_tokens != sorted(shared_tokens):
            raise ValueError("shared_numeric_tokens must be sorted")
        if len(shared_tokens) != len(set(shared_tokens)):
            raise ValueError("shared_numeric_tokens must not contain duplicates")

        expected_norm_refs = set([self.identity.normalized_a, self.identity.normalized_b])
        if set(norm_refs) != expected_norm_refs:
            raise ValueError("normalized_references values do not match identity")

        if set(shared_tokens) != set(self.identity.shared_numeric_tokens):
            raise ValueError("shared_numeric_tokens values do not match identity")

def enrich_reference_identity(
    identity: ReferenceIdentityEvidence,
    profile: ReferenceCorpusProfile,
) -> EnrichedReferenceEvidence:
    unique_norm_refs = sorted(list(set([identity.normalized_a, identity.normalized_b])))

    norm_evidence = []
    for ref in unique_norm_refs:
        if ref in profile.normalized_reference_frequency:
            stats = NormalizedReferenceStatistics(
                normalized_reference=ref,
                frequency=profile.normalized_reference_frequency[ref]
            )
        else:
            stats = None
        norm_evidence.append(NormalizedReferenceEvidence(normalized_reference=ref, statistics=stats))

    token_evidence = []
    for token in identity.shared_numeric_tokens:
        if token in profile.numeric_token_document_frequency:
            token_stats = ReferenceTokenStatistics(
                token=token,
                document_frequency=profile.numeric_token_document_frequency[token]
            )
        else:
            token_stats = None
        token_evidence.append(SharedNumericTokenEvidence(token=token, statistics=token_stats))

    return EnrichedReferenceEvidence(
        identity=identity,
        reference_count=profile.reference_count,
        normalized_references=tuple(norm_evidence),
        shared_numeric_tokens=tuple(token_evidence),
    )

@dataclass(frozen=True)
class ReferenceEvidencePolicy:
    short_token_max_length: int = 2
    medium_token_max_length: int = 4
    short_token_fallback: float = 0.10
    medium_token_fallback: float = 0.30
    long_token_fallback: float = 0.60
    exact_reference_fallback: float = 0.60
    repeated_pattern_discount: float = 0.50

    def __post_init__(self) -> None:
        import math
        if self.short_token_max_length < 1:
            raise ValueError("short_token_max_length must be >= 1")
        if self.medium_token_max_length <= self.short_token_max_length:
            raise ValueError("medium_token_max_length must be > short_token_max_length")

        # Basic float bounds
        for val in (self.short_token_fallback,
            self.medium_token_fallback,
            self.long_token_fallback,
            self.exact_reference_fallback,
            self.repeated_pattern_discount):
            
            if math.isnan(val) or math.isinf(val):
                raise ValueError("Float parameters cannot be NaN or infinity")
            if not (0.0 <= val <= 1.0):
                raise ValueError("All float parameters must be between 0.0 and 1.0")

        if not (self.short_token_fallback <= self.medium_token_fallback <= self.long_token_fallback):
            raise ValueError("Fallbacks must be monotonically non-decreasing")

        if self.long_token_fallback > 0.75:
            raise ValueError("long_token_fallback must be <= 0.75 for safety")
            
        if self.exact_reference_fallback > 0.75:
            raise ValueError("exact_reference_fallback must be <= 0.75 for safety")

class ReferenceEvidenceKind(StrEnum):
    NORMALIZED_REFERENCE = "normalized_reference"
    SHARED_NUMERIC_TOKEN = "shared_numeric_token"

@dataclass(frozen=True)
class ReferenceEvidenceContribution:
    evidence_kind: ReferenceEvidenceKind
    identity_value: str
    positive_evidence: float
    evidential_weight: float
    statistics_available: bool

    def __post_init__(self) -> None:
        if not self.identity_value:
            raise ValueError("identity_value cannot be empty")
        
        import math
        if not math.isfinite(self.positive_evidence):
            raise ValueError("positive_evidence must be finite")
        if not (0.0 <= self.positive_evidence <= 1.0):
            raise ValueError("positive_evidence must be between 0.0 and 1.0")

        if not math.isfinite(self.evidential_weight):
            raise ValueError("evidential_weight must be finite")
        if not (0.0 <= self.evidential_weight <= 1.0):
            raise ValueError("evidential_weight must be between 0.0 and 1.0")

        if self.evidence_kind == ReferenceEvidenceKind.SHARED_NUMERIC_TOKEN:
            if not self.identity_value.isdigit():
                raise ValueError("SHARED_NUMERIC_TOKEN identity_value must be numeric")
        
        if self.evidence_kind == ReferenceEvidenceKind.NORMALIZED_REFERENCE:
            from recongraph.normalization.text import normalize_reference
            if normalize_reference(self.identity_value) != self.identity_value:
                raise ValueError("NORMALIZED_REFERENCE identity_value must be normalized")

@dataclass(frozen=True)
class ReferenceEvidenceInterpretation:
    score: float
    statistical_coverage: float
    contributions: tuple[ReferenceEvidenceContribution, ...]

    def __post_init__(self) -> None:
        import math
        if not math.isfinite(self.score):
            raise ValueError("score must be finite")
        if not (0.0 <= self.score <= 1.0):
            raise ValueError("score must be between 0.0 and 1.0")
            
        if not math.isfinite(self.statistical_coverage):
            raise ValueError("statistical_coverage must be finite")
        if not (0.0 <= self.statistical_coverage <= 1.0):
            raise ValueError("statistical_coverage must be between 0.0 and 1.0")

        if not self.contributions:
            if self.score != 0.0 or self.statistical_coverage != 0.0:
                raise ValueError("empty contributions requires score=0.0 and statistical_coverage=0.0")
            return

        max_score = max(c.positive_evidence for c in self.contributions)
        if not math.isclose(self.score, max_score, abs_tol=1e-9):
            raise ValueError("score must equal the strongest contribution magnitude")

        if self.statistical_coverage not in {0.0, 1.0}:
            raise ValueError("statistical_coverage must be binary (0.0 or 1.0) under strongest-unit interpretation")

def _profiled_rarity_magnitude(
    frequency: int,
    reference_count: int,
) -> float:
    if frequency < 1:
        raise ValueError("frequency must be >= 1")
    if reference_count < 1:
        raise ValueError("reference_count must be >= 1")
    if frequency > reference_count:
        raise ValueError("frequency cannot exceed reference_count")
        
    import math
    return 1.0 - math.sqrt(frequency / reference_count)

def _structural_token_magnitude(
    token: str,
    policy: ReferenceEvidencePolicy,
) -> float:
    if not token or not token.isdigit():
        raise ValueError("invalid numeric token")

    n = len(token)
    if n <= policy.short_token_max_length:
        base_magnitude = policy.short_token_fallback
    elif n <= policy.medium_token_max_length:
        base_magnitude = policy.medium_token_fallback
    else:
        base_magnitude = policy.long_token_fallback

    # Single-symbol repetition detection
    if len(set(token)) == 1:
        return base_magnitude * policy.repeated_pattern_discount
        
    return base_magnitude

def _construct_reference_evidence_contributions(
    evidence: EnrichedReferenceEvidence,
    policy: ReferenceEvidencePolicy,
) -> tuple[ReferenceEvidenceContribution, ...]:
    contributions = []

    if evidence.identity.exact_normalized_match:
        # 1. Exact normalized full-reference identity is the primary evidence unit
        # 2. Shared numeric tokens are bypassed completely
        # 3. Exactly ONE contribution is produced
        norm_ev = evidence.normalized_references[0]
        
        if norm_ev.statistics is not None:
            evidential_weight = _profiled_rarity_magnitude(
                frequency=norm_ev.statistics.frequency,
                reference_count=evidence.reference_count,
            )
            stats_available = True
        else:
            evidential_weight = policy.exact_reference_fallback
            stats_available = False
            
        contributions.append(ReferenceEvidenceContribution(
            evidence_kind=ReferenceEvidenceKind.NORMALIZED_REFERENCE,
            identity_value=norm_ev.normalized_reference,
            positive_evidence=1.0,
            evidential_weight=evidential_weight,
            statistics_available=stats_available,
        ))
    else:
        # Construct one contribution for EACH shared numeric token
        for token_ev in evidence.shared_numeric_tokens:
            if token_ev.statistics is not None:
                evidential_weight = _profiled_rarity_magnitude(
                    frequency=token_ev.statistics.document_frequency,
                    reference_count=evidence.reference_count,
                )
                stats_available = True
            else:
                evidential_weight = _structural_token_magnitude(
                    token=token_ev.token,
                    policy=policy,
                )
                stats_available = False
                
            contributions.append(ReferenceEvidenceContribution(
                evidence_kind=ReferenceEvidenceKind.SHARED_NUMERIC_TOKEN,
                identity_value=token_ev.token,
                positive_evidence=0.5,
                evidential_weight=evidential_weight,
                statistics_available=stats_available,
            ))
            
    return tuple(contributions)

def _select_strongest_reference_contribution(
    contributions: tuple[ReferenceEvidenceContribution, ...],
) -> ReferenceEvidenceContribution:
    if not contributions:
        raise ValueError("at least one reference evidence contribution is required")

    def sort_key(c: ReferenceEvidenceContribution) -> tuple[float, float, bool]:
        return (c.positive_evidence, c.evidential_weight, c.statistics_available)

    return max(contributions, key=sort_key)

def _assemble_reference_evidence_interpretation(
    contributions: tuple[ReferenceEvidenceContribution, ...],
) -> ReferenceEvidenceInterpretation:
    winner = _select_strongest_reference_contribution(contributions)
    
    return ReferenceEvidenceInterpretation(
        score=winner.positive_evidence,
        statistical_coverage=1.0 if winner.statistics_available else 0.0,
        contributions=contributions
    )

def interpret_reference_evidence(
    evidence: EnrichedReferenceEvidence,
    policy: ReferenceEvidencePolicy,
) -> ReferenceEvidenceInterpretation:
    contributions = _construct_reference_evidence_contributions(evidence, policy)
    
    if not contributions:
        return ReferenceEvidenceInterpretation(
            score=0.0,
            statistical_coverage=0.0,
            contributions=()
        )
        
    return _assemble_reference_evidence_interpretation(contributions)

@dataclass(frozen=True)
class ReferenceEvidenceContext:
    profile: ReferenceCorpusProfile
    policy: ReferenceEvidencePolicy

def compute_reference_interpretation(
    reference_a: str | None,
    reference_b: str | None,
    context: ReferenceEvidenceContext,
) -> ReferenceEvidenceInterpretation:
    identity = extract_reference_identity(reference_a, reference_b)
    
    if identity is None:
        return ReferenceEvidenceInterpretation(
            score=0.0,
            statistical_coverage=0.0,
            contributions=()
        )
        
    enriched = enrich_reference_identity(identity, context.profile)
    return interpret_reference_evidence(enriched, context.policy)
