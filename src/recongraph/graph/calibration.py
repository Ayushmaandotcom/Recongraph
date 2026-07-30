from dataclasses import dataclass
from typing import Mapping, Sequence

from recongraph.contrib.kernel.assertions import EvidenceAssertion, AssertionPolarity
from recongraph.graph.dempster_shafer import MassFunction

@dataclass(frozen=True)
class CalibrationCurve:
    """
    A monotonic mapping from raw magnitude [0, 1] to empirical probability [0, 1].
    points must be sorted by magnitude in ascending order.
    """
    points: tuple[tuple[float, float], ...] # (magnitude, calibrated_mass)

    def interpolate(self, x: float) -> float:
        """Linearly interpolate the calibrated mass for a given magnitude x."""
        if not self.points:
            return x # Identity if empty
        
        if x <= self.points[0][0]:
            return self.points[0][1]
        
        if x >= self.points[-1][0]:
            return self.points[-1][1]
            
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i+1]
            if x1 <= x <= x2:
                if x2 == x1:
                    return y1
                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)
                
        return self.points[-1][1]

@dataclass(frozen=True)
class CalibrationPolicy:
    """Stores calibration curves for various Claim / Provider combinations."""
    # Mapping of (claim_id, provider_name) -> CalibrationCurve
    curves: Mapping[tuple[str, str], CalibrationCurve]
    
    # Fallback default mapping when specific curve is absent
    default_curve: CalibrationCurve = CalibrationCurve(((0.0, 0.0), (1.0, 1.0)))

    def get_curve(self, claim_id: str, provider_name: str) -> CalibrationCurve:
        return self.curves.get((claim_id, provider_name), self.default_curve)

class CalibrationEngine:
    """
    Converts a raw EvidenceAssertion into a mathematically rigorous Dempster-Shafer
    MassFunction based on empirical precision tracking.
    """
    def __init__(self, policy: CalibrationPolicy):
        self.policy = policy
        
    def calibrate(self, assertion: EvidenceAssertion) -> MassFunction:
        claim_id = assertion.proposition.claim.claim_id.value
        provider = assertion.authority.basis.value
        
        curve = self.policy.get_curve(claim_id, provider)
        calibrated_mag = curve.interpolate(assertion.magnitude)
        
        return MassFunction.from_calibrated(assertion.polarity, calibrated_mag)
