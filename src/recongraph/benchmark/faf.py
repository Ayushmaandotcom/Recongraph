import os
import json
from dataclasses import asdict
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.engine import ReconciliationResult
from recongraph.synthetic.models import ScenarioSpecification, ExpectedOutcome
from recongraph.graph.decision import DecisionAction

def _format_dict(d: dict) -> str:
    return json.dumps(d, indent=2, default=str)

def generate_faf_report(
    scenario: ScenarioSpecification, 
    purchases: list[PurchaseRecord],
    gsts: list[GSTRecord],
    result: ReconciliationResult,
    actual_decision: DecisionAction,
    output_dir: str = "faf_reports"
) -> None:
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.join(output_dir, f"{scenario.scenario_id}.md")
    
    # Extract evidence from the chosen hypothesis (if any)
    evidence_str = "No specific hypothesis selected."
    if result.auto_matches and result.auto_matches[0].selected_hypothesis:
        eh = result.auto_matches[0].selected_hypothesis
        evidence_str = f"Score: {eh.score:.4f}\nCoverage: {eh.coverage:.4f}\nSignals: {_format_dict(eh.supporting_evidence.signals)}"
    elif result.review_packets and result.review_packets[0].selected_hypothesis:
        eh = result.review_packets[0].selected_hypothesis
        evidence_str = f"Score: {eh.score:.4f}\nCoverage: {eh.coverage:.4f}\nSignals: {_format_dict(eh.supporting_evidence.signals)}"

    traces_str = ""
    for idx, trace in enumerate(result.traces):
        traces_str += f"### Trace ID: {trace.trace_id}\n"
        for event in trace.events:
            traces_str += f"- `{event.timestamp.isoformat()}`: [{event.stage}] {type(event.payload).__name__}\n"

    content = f"""# FAF Report: {scenario.scenario_id}

## 1. Scenario Summary
**Difficulty:** {scenario.difficulty.value}
**Expected Decision:** `{scenario.expected_outcome.expected_decision.value}`
**Actual Decision:** `{actual_decision.value}`

## 2. Input Data
### Purchases
```json
{_format_dict([asdict(p) for p in purchases])}
```

### GSTs
```json
{_format_dict([asdict(g) for g in gsts])}
```

## 3. Evidence & Fusion Output
```text
{evidence_str}
```

## 4. Traces
{traces_str}
"""

    with open(filename, "w") as f:
        f.write(content)
