import re

def rep(filepath, old, new):
    with open(filepath, "r") as f:
        content = f.read()
    with open(filepath, "w") as f:
        f.write(content.replace(old, new))

rep("src/recongraph/domain/reliability/adapter.py", "min_y = min_y", "min_y = float(min_y.y0) if hasattr(min_y, 'y0') else float(min_y)")
rep("src/recongraph/synthetic/reconbench.py", "mutations = []", "from typing import Any\n    mutations: list[tuple[int, Any]] = []")
rep("tests/test_trace_semantic_mutations.py", "ScoringEvidence(relationship=DummyRel())", "ScoringEvidence(relationship=None)")
rep("tests/test_record_conservation.py", "def test_exact_conservation_simple(self):", "def test_exact_conservation_simple(self) -> None:")
rep("tests/test_record_conservation.py", "def test_exact_conservation_multi_record(self):", "def test_exact_conservation_multi_record(self) -> None:")
rep("src/recongraph/benchmark/runner.py", "providers: Sequence[Any]", "providers: list[Any]")
rep("src/recongraph/benchmark/calibration.py", "providers: Sequence[Any]", "providers: list[Any]")
rep("src/recongraph/benchmark/runner.py", "Sequence[EvidenceProvider]", "list[EvidenceProvider]")
rep("src/recongraph/benchmark/calibration.py", "Sequence[EvidenceProvider]", "list[EvidenceProvider]")
rep("src/recongraph/engine.py", "providers: Sequence[EvidenceProvider]", "providers: list[EvidenceProvider]")
rep("src/recongraph/benchmark/calibration.py", "metric.precision", "metric.precision if metric else 0.0")
rep("src/recongraph/benchmark/calibration.py", "metric.recall", "metric.recall if metric else 0.0")
rep("src/recongraph/benchmark/calibration.py", "metric.f1_score", "metric.f1_score if metric else 0.0")
rep("src/recongraph/benchmark/calibration.py", "metric.review_reduction_rate", "metric.review_reduction_rate if metric else 0.0")

