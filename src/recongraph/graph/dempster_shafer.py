from dataclasses import dataclass
from recongraph.contrib.kernel.assertions import AssertionPolarity

@dataclass(frozen=True)
class MassFunction:
    """
    Represents a Basic Belief Assignment (BBA) in Dempster-Shafer Theory
    over the frame of discernment {Match, NoMatch}.
    """
    match: float       # m({Match})
    no_match: float    # m({NoMatch})
    uncertainty: float # m({Match, NoMatch})

    def __post_init__(self):
        total = self.match + self.no_match + self.uncertainty
        if not abs(total - 1.0) < 1e-5:
            raise ValueError(f"Mass function must sum to 1.0, got {total}")

    @classmethod
    def from_calibrated(cls, polarity: AssertionPolarity, calibrated_magnitude: float) -> 'MassFunction':
        """
        Convert a calibrated empirical probability into a Mass Function.
        """
        # Ensure magnitude is within [0, 1]
        mag = max(0.0, min(1.0, calibrated_magnitude))
        
        if polarity == AssertionPolarity.SUPPORT:
            return cls(match=mag, no_match=0.0, uncertainty=1.0 - mag)
        elif polarity == AssertionPolarity.CONFLICT:
            return cls(match=0.0, no_match=mag, uncertainty=1.0 - mag)
        else:
            # Neutral / Unsupported implies total uncertainty
            return cls(match=0.0, no_match=0.0, uncertainty=1.0)

    def combine(self, other: 'MassFunction') -> 'MassFunction':
        """
        Dempster's Rule of Combination.
        """
        # Compute intersections
        # m1(M) * m2(M) -> M
        # m1(M) * m2(U) -> M
        # m1(U) * m2(M) -> M
        match_intersection = (self.match * other.match) + (self.match * other.uncertainty) + (self.uncertainty * other.match)
        
        # m1(NM) * m2(NM) -> NM
        # m1(NM) * m2(U) -> NM
        # m1(U) * m2(NM) -> NM
        no_match_intersection = (self.no_match * other.no_match) + (self.no_match * other.uncertainty) + (self.uncertainty * other.no_match)
        
        # m1(U) * m2(U) -> U
        uncertainty_intersection = self.uncertainty * other.uncertainty
        
        # Compute Conflict (K)
        # m1(M) * m2(NM) -> Empty Set
        # m1(NM) * m2(M) -> Empty Set
        k = (self.match * other.no_match) + (self.no_match * other.match)
        
        if k >= 1.0:
            # Absolute contradiction. Fallback to total uncertainty.
            return MassFunction(match=0.0, no_match=0.0, uncertainty=1.0)
            
        normalization_factor = 1.0 / (1.0 - k)
        
        return MassFunction(
            match=match_intersection * normalization_factor,
            no_match=no_match_intersection * normalization_factor,
            uncertainty=uncertainty_intersection * normalization_factor
        )

    @property
    def belief(self) -> float:
        """Belief in Match (lower bound)"""
        return self.match

    @property
    def plausibility(self) -> float:
        """Plausibility of Match (upper bound)"""
        return self.match + self.uncertainty
