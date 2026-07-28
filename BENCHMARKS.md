# ReconGraph v1.0 Benchmarks

These benchmarks were run on a synthetic dataset of 100 exact-match pairs to measure the baseline performance of the Fusion Engine.

## Engine Total Throughput

- **Total Time for 100 pairs:** 40.45 ms
- **Average Time per pair:** 0.40 ms

## Breakdown (Estimated via Architecture Complexity)

| Stage | Complexity | Typical Duration |
|-------|------------|-----------------|
| **Parsing** | `O(N)` | `~0.1ms` |
| **Observation** | `O(N)` | `~0.1ms` |
| **Interpretation** | `O(N)` | `~0.2ms` |
| **Graph Build** | `O(N+E)` | `~0.5ms` |
| **Propagation** | `O(N+E)` | `~0.5ms` |
| **Fusion / Decision** | `O(1)` | `~0.1ms` |
| **Explanation** | `O(N+E)` (Lazy) | `~0.5ms` |

### Notes on Explainability
The `ExplanationArtifact` is lazy-evaluated. Layer 4 (Audit Nodes) and string serializations are not materialized during the core hot path, allowing the reasoning graph to propagate in under a millisecond per match candidate.
