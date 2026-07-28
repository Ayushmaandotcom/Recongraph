"""
Default-policy protection test.

Guards the DecisionPolicy.auto_match_threshold default against silent regression.

CALIBRATION BASIS (reconbench sweep, seed=42, n=500, 2026-07-29):
  Threshold | Exact Recall | Noisy Pos Recall | Adv FP | Noisy Pos FP
  -------------------------------------------------------------------
     0.85   |   1.0000     |      1.0000      |   0    |      37
     0.90   |   1.0000     |      1.0000      |   0    |      37
     0.95   |   1.0000     |      0.9952      |   0    |      37
     0.99   |   1.0000     |      0.6812      |   0    |       1

0.95 is the highest threshold that keeps zero false positives on adversarial 
negatives and passes the referee, while maximizing recall on noisy positives 
(±₹1-5 rounding gaps, 1-3 day date drifts). 

DO NOT LOWER THIS DEFAULT without re-running the sweep and publishing
an updated dual-table in BENCHMARKS.md.
"""

from recongraph.graph.decision import DecisionPolicy
from recongraph.config import DecisionConfig, ReconGraphConfig


def test_default_auto_match_threshold_is_0_95() -> None:
    """The default auto_match_threshold must be exactly 0.95 (calibrated 2026-07-29)."""
    policy = DecisionPolicy()
    assert policy.auto_match_threshold == 0.95, (
        f"DEFAULT REGRESSION: auto_match_threshold is {policy.auto_match_threshold!r}, "
        f"expected 0.95. See calibration table in this file before changing."
    )


def test_default_minimum_coverage_threshold_is_0_80() -> None:
    """The minimum coverage threshold governs whether a high-score result auto-matches.
    0.80 means at least 80% of the signal weights must have non-None scores.
    Lowering this allows auto-matches with missing evidence (e.g. absent tax signal)."""
    policy = DecisionPolicy()
    assert policy.minimum_coverage_threshold == 0.80, (
        f"DEFAULT REGRESSION: minimum_coverage_threshold is "
        f"{policy.minimum_coverage_threshold!r}, expected 0.80."
    )


def test_decision_config_propagates_default_policy() -> None:
    """DecisionConfig must use DecisionPolicy defaults unchanged."""
    config = DecisionConfig()
    assert config.policy.auto_match_threshold == 0.95
    assert config.policy.minimum_coverage_threshold == 0.80


def test_recon_graph_config_propagates_default_policy() -> None:
    """ReconGraphConfig end-to-end: top-level config must carry 0.95 threshold."""
    config = ReconGraphConfig()
    assert config.decision_config.policy.auto_match_threshold == 0.95
