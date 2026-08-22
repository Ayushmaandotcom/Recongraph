import subprocess
import os

def run_evaluation():
    print("========================================")
    print("ReconGraph Phase 7 Evaluation Pipeline")
    print("========================================")

    steps = [
        ("Extracting Training Dataset", "python scripts/build_feedback_dataset.py"),
        ("Training Champion & Challenger Models", "python -c 'from recongraph.learning.candidate_model import train_model; from pathlib import Path; train_model(Path(\"datasets/training/feedback_dataset.csv\"))'"),
        ("Analyzing Decision Boundaries", "python scripts/analyze_decision_boundaries.py"),
        ("Running Performance Benchmarks", "python scripts/run_benchmarks.py"),
        ("Evaluating Hallucination Detection", "pytest src/recongraph/benchmark/explanation_evaluator.py -v"),
    ]

    for name, cmd in steps:
        print(f"\n---> {name}")
        try:
            subprocess.run(cmd, shell=True, check=True)
            print("[SUCCESS]")
        except subprocess.CalledProcessError as e:
            print(f"[FAILED] Error in step '{name}'. Check logs.")
            return

    print("\n========================================")
    print("Evaluation Complete. All artifacts generated in 'reports/'.")
    print("========================================")

if __name__ == "__main__":
    run_evaluation()
