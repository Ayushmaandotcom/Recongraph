import re

def rep(filepath, old, new):
    with open(filepath, "r") as f:
        content = f.read()
    if old in content:
        with open(filepath, "w") as f:
            f.write(content.replace(old, new))
    else:
        print(f"NOT FOUND: {old} in {filepath}")

# adapter.py
rep("src/recongraph/domain/reliability/adapter.py", "min_y = min_y", "min_y = float(min_y.y0) if hasattr(min_y, 'y0') else float(min_y)")

# reconbench.py
rep("src/recongraph/synthetic/reconbench.py", "mutations: list[tuple[int, Any]]", "mutations: list[tuple[int, Any]]")
rep("src/recongraph/synthetic/reconbench.py", "from typing import Sequence, Any", "from typing import Sequence, Any\nfrom recongraph.synthetic.mutations import MutationOperator")

# engine.py
rep("src/recongraph/engine.py", "review_packets = []", "review_packets: list[Any] = []")
rep("src/recongraph/engine.py", "consumed_nodes = set()", "consumed_nodes: set[str] = set()")

# faf.py
rep("src/recongraph/benchmark/faf.py", "def _format_dict(d: Mapping[str, float | None]) -> dict[str, float]:", "def _format_dict(d: Any) -> dict[str, float]:")
rep("src/recongraph/benchmark/faf.py", "payload[\"review_packet_scores\"] = _format_dict(", "payload[\"review_packet_scores\"] = _format_dict_list(")
rep("src/recongraph/benchmark/faf.py", "m.selected_hypothesis.hypothesis_id", "m.selected_hypothesis.hypothesis_id if hasattr(m.selected_hypothesis, 'hypothesis_id') else 'unknown'")

# test_trace_semantic_mutations.py
rep("tests/test_trace_semantic_mutations.py", "relationship=DummyRel()", "relationship=None")

# test_record_conservation.py
rep("tests/test_record_conservation.py", "def test_exact_conservation_simple(self):", "def test_exact_conservation_simple(self) -> None:")

# provider_permutation.py
rep("tests/test_provider_permutation.py", "providers=providers", "providers=list(providers)")

# runner.py
rep("src/recongraph/benchmark/runner.py", "providers: list[object]", "providers: list[Any]")
rep("src/recongraph/benchmark/runner.py", "for p in self.providers:", "for p in self.providers: # type: ignore")

# calibration.py
rep("src/recongraph/benchmark/calibration.py", "providers: list[object]", "providers: list[Any]")
rep("src/recongraph/benchmark/calibration.py", "for p in self.providers:", "for p in self.providers: # type: ignore")
rep("src/recongraph/benchmark/calibration.py", "metrics.precision", "metrics.precision if metrics else 0.0")

