import os
import re

TEST_FILES = [
    "tests/test_benchmark_runner.py",
    "tests/test_candidate_generation.py",
    "tests/test_engine.py",
    "tests/test_golden_path.py",
    "tests/test_hypothesis_evaluator.py",
    "tests/test_properties.py",
    "tests/test_provider_permutation.py",
    "tests/test_trace_identity.py",
    "tests/test_shadow_evaluation.py"
]

def fix_file(file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r") as f:
        content = f.read()

    # We need to find block of `providers = [...]` or `[` containing FinancialEvidenceProvider 
    # A simple approach: 
    # Any block from `[` to `]` that contains `FinancialEvidenceProvider` should have `SemanticEvidenceProvider()` at the end.
    
    parts = content.split("]")
    for i in range(len(parts) - 1):
        if "FinancialEvidenceProvider" in parts[i] and "SemanticEvidenceProvider" not in parts[i]:
            parts[i] += ",\n        SemanticEvidenceProvider()"
            
    content = "]".join(parts)

    with open(file_path, "w") as f:
        f.write(content)

for f in TEST_FILES:
    fix_file(f)

print("Tests updated.")
