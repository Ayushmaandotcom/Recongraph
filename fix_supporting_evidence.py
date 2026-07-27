import os
import re

def fix_file(path):
    with open(path, "r") as f:
        content = f.read()

    orig_content = content

    # src/recongraph/engine.py
    if "engine.py" in path:
        content = content.replace(
            'contributions = h.supporting_evidence.get("contributions", {})',
            'contributions = h.supporting_evidence.contributions'
        )

    # src/recongraph/graph/explainability.py
    if "explainability.py" in path:
        content = content.replace(
            'signals = hypothesis.supporting_evidence.get("signals", {})',
            'signals = hypothesis.supporting_evidence.signals'
        )
        content = content.replace(
            'metadata = hypothesis.supporting_evidence.get("metadata", {})',
            'metadata = hypothesis.supporting_evidence.metadata'
        )

    # src/recongraph/graph/trace.py
    if "trace.py" in path:
        content = content.replace(
            'if "relationship" in h.supporting_evidence:',
            'if h.supporting_evidence.relationship is not None:'
        )
        content = content.replace(
            'rel = h.supporting_evidence["relationship"]',
            'rel = h.supporting_evidence.relationship'
        )
        content = content.replace(
            'list(h.supporting_evidence.get("metadata", {}).keys())',
            'list(h.supporting_evidence.metadata.keys())'
        )

    # tests
    if path.startswith("tests/"):
        # Fix initialization: supporting_evidence={} -> supporting_evidence=ScoringEvidence()
        content = re.sub(
            r'supporting_evidence\s*=\s*\{\s*\}',
            'supporting_evidence=ScoringEvidence()',
            content
        )
        
        # supporting_evidence={"signals": ...} -> supporting_evidence=ScoringEvidence(signals=...)
        # We'll use a regex for the simple cases
        content = re.sub(
            r'supporting_evidence\s*=\s*\{\s*"signals"\s*:\s*([^,]+),\s*"metadata"\s*:\s*([^\}]+)\s*\}',
            r'supporting_evidence=ScoringEvidence(signals=\1, metadata=\2)',
            content
        )
        content = re.sub(
            r'supporting_evidence\s*=\s*\{\s*"signals"\s*:\s*(\{\})\s*\}',
            r'supporting_evidence=ScoringEvidence(signals=\1)',
            content
        )
        
        # Array/dict accesses
        content = content.replace(
            'result.supporting_evidence["signals"][',
            'result.supporting_evidence.signals['
        )
        content = content.replace(
            'decision.selected_hypothesis.supporting_evidence["contributions"]',
            'decision.selected_hypothesis.supporting_evidence.contributions'
        )
        content = content.replace(
            'h_proj.supporting_evidence["metadata"]["new_plugin"] = {}',
            'h_proj.supporting_evidence.metadata["new_plugin"] = {}'
        )
        
        # Add import for ScoringEvidence if ScoringEvidence is used
        if "ScoringEvidence" in content and "from recongraph.matching.scoring import ScoringEvidence" not in content:
            content = "from recongraph.matching.scoring import ScoringEvidence\n" + content

    if content != orig_content:
        with open(path, "w") as f:
            f.write(content)
        print(f"Fixed {path}")

for root, _, files in os.walk("src"):
    for file in files:
        if file.endswith(".py"):
            fix_file(os.path.join(root, file))
            
for root, _, files in os.walk("tests"):
    for file in files:
        if file.endswith(".py"):
            fix_file(os.path.join(root, file))

