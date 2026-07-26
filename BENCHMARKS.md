# ReconGraph Benchmarking Methodology

ReconGraph includes a rigorous, deterministic benchmarking framework located in `src/recongraph/benchmark`.

## Reproducible Benchmarking

To ensure that engine optimizations (e.g. graph partitioning, pair interpretation) do not regress precision, recall, or runtime performance, ReconGraph provides a standard command-line harness.

### Running Benchmarks

```bash
python -m recongraph.benchmark.runner --profile full
```

### Metrics Collected

The benchmarking framework measures:

- **Parsing Time**: Latency introduced by external providers parsing unstructured inputs.
- **Observation Latency**: Time to wrap raw data in `ReliabilityEnvelope`s.
- **Graph Construction (N x M)**: Time complexity of building the bipartite Candidate Graph based on blocking keys.
- **Hypothesis Evaluation**: The bottleneck. Time spent evaluating semantic projection rules on hypotheses.
- **Fusion & Decision**: Overhead of resolving graph constraints into a `DecisionTrace`.

### Memory Footprint

ReconGraph is designed to be highly memory efficient. Benchmarks track peak memory allocations. The use of `__slots__` and frozen dataclasses (e.g., `ReliabilityProfile`) guarantees a strict upper bound on memory consumption per record.
