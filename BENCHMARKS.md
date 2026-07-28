# ReconGraph v1.0 Benchmarks

These benchmarks were run on a synthetic dataset of 100 exact-match pairs to measure the baseline performance of the Fusion Engine.

## Engine Total Throughput

- **Total Time for 100 pairs:** 43.19 ms
# ReconGraph V1 Benchmark Report

## Operational Envelope (N = 10,000)
The ReconGraph decision engine has been successfully stress-tested on a 10,000 Purchase × 10,000 GST Record corpus, evaluating **100 million potential pairs** dynamically.

### Execution Metrics
- **Corpus Size:** 10,000 Purchase Records, 10,000 GST Records
- **Wall Time (End-to-End):** 2824.59 seconds (~47 minutes)
- **Peak Memory (Resident):** 994.64 MB (Engine Memory: 949.05 MB)

### Calibration Baseline
Using grid-search threshold optimization (`experiments/calibrate_thresholds.py`), the legacy fallback engine yields the following core metrics at optimal threshold configuration:

- **Optimal Auto-Match Threshold:** `0.85`
- **Precision:** `0.9127`
- **Recall:** `0.9021`
- **F1 Score:** `0.9074`

*Epistemic Caveat: The FP floor of exactly 37 at every threshold is a property of the synthetic generator's noise model, not of real data. This default of 0.85 is calibrated explicitly on synthetic corpus v1, seed 42.*

*Note on Scale Execution:*
During scale experiments, the graph dynamically limits component traversal for subsets exceeding 15 candidate edges to prevent O(2^N) backtracking explosion on highly entangled clusters. These dense clusters immediately degrade to `REVIEW_AMBIGUOUS` packets, ensuring deterministic completion time.

### Provenance Overhead
- **Full Engine Trace Storage:** Supports graph-level and hypothesis-level tracing in memory. Overhead is bounded strictly by the configured oversized-component cutoff.

## Future Projections (N=100k)
With parallelization across unconnected candidate components, the runtime for 100k pairs is mathematically bounded, provided the block collision density remains bounded. Future work must replace the DFS backtrack `HypothesisSearcher` with an assignment algorithm for denser components.
