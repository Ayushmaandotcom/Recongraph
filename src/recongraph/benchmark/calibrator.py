import json
from dataclasses import dataclass
from typing import Mapping, Sequence, Any
from collections import defaultdict
import numpy as np

from recongraph.graph.calibration import CalibrationCurve, CalibrationPolicy
from recongraph.contrib.kernel.assertions import EvidenceAssertion

@dataclass
class CalibratorResult:
    policy: CalibrationPolicy
    metrics: dict[str, Any]

class ConfidenceCalibrator:
    """
    Consumes a dataset of (Assertion, is_match) and outputs a CalibrationPolicy.
    """
    def __init__(self, num_bins: int = 10):
        self.num_bins = num_bins
        
    def calibrate(self, dataset: Sequence[tuple[EvidenceAssertion, bool]]) -> CalibratorResult:
        # Group by (claim_id, provider)
        grouped_data: dict[tuple[str, str], list[tuple[float, bool]]] = defaultdict(list)
        
        for assertion, is_match in dataset:
            claim_id = assertion.proposition.claim.claim_id.value
            provider = assertion.authority.basis.value
            mag = assertion.magnitude
            grouped_data[(claim_id, provider)].append((mag, is_match))
            
        curves = {}
        metrics = {}
        
        for key, items in grouped_data.items():
            # Bin the magnitudes and compute empirical precision
            bins = np.linspace(0.0, 1.0, self.num_bins + 1)
            points = [(0.0, 0.0)] # Always start at 0, 0
            
            for i in range(len(bins) - 1):
                lower = bins[i]
                upper = bins[i+1]
                
                # Get items in this bin
                bin_items = [item for item in items if lower <= item[0] <= upper]
                if not bin_items:
                    continue
                    
                matches = sum(1 for _, is_match in bin_items if is_match)
                precision = matches / len(bin_items)
                
                midpoint = (lower + upper) / 2.0
                
                # Enforce monotonicity
                calibrated_mass = max(points[-1][1], precision)
                points.append((midpoint, calibrated_mass))
                
            # Add final point at 1.0
            if points[-1][0] < 1.0:
                points.append((1.0, points[-1][1]))
                
            curves[key] = CalibrationCurve(tuple(points))
            metrics[f"{key[0]}_{key[1]}"] = {"points": points, "samples": len(items)}
            
        policy = CalibrationPolicy(curves=curves)
        return CalibratorResult(policy=policy, metrics=metrics)
