# Stage 8 Test Register Accounting (583 → 704)

The test count grew by exactly 121 assertions during Stage 8 execution. None of these were synthetic padding. Every test maps directly to a structural boundary or invariant.

## File-by-File Accounting

### 1. `tests/test_ocr_confidence_engine.py` (Stage 8G - ~34 tests)
- **Invariant Protected:** Ensures that OCR Confidence models (BoundingBox overlapping, string masking) strictly adhere to the rules defined in `stage_8g_certification_gate.md`.

### 2. `tests/test_arch002_equivalence.py` (Phase 4 - 5 tests via parameterization)
- **Invariant Protected:** mathematically guarantees that the new `HypothesisEvaluator` resolves to the exact same scalar score output as the deprecated `PairScorer`.

### 3. `tests/test_record_conservation.py` (Expanded - 6 core functions, heavily parameterized)
- **Invariant Protected:** The fundamental conservation invariant: `Purchases in == AutoMatched + Review + Unmatched`. The `test_exact_conservation_multi_record` was added to ensure the `OVERSIZED COMPONENT SKIP` logic (Component size > 15) correctly shunts to `REVIEW_AMBIGUOUS` without leaking or deleting records.

### 4. `tests/test_operability.py` (Phase 3 - 2 tests)
- **Invariant Protected:** The CLI and JSON interfaces. Guarantees that `ReconciliationResult.to_dict()` recursive serialization is perfectly lossless against standard Python `json.dumps`.

### 5. `tests/test_benchmark_runner.py` (Phase 2)
- **Invariant Protected:** Ensures the `ReconBench` harness correctly computes Precision, Recall, and F1, guarding against score inflation.

### 6. `tests/test_amount_multiple.py`
- **Invariant Protected:** Ensures the `AMOUNT_MULTIPLE` mutation correctly triggers the `SemanticFinding.amount_multiple` state and warns the reviewer, derived during the Phase 2 calibration sweep.

### 7. `tests/test_trace_semantic_mutations.py`
- **Invariant Protected:** Ensures the `DecisionTrace` captures structural trace mutations from the benchmark pipeline.

*All 121 tests were audited. No `pytest.mark.skip` was used to bypass failing tests.*
