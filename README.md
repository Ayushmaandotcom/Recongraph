# ReconGraph

[![Tests](https://github.com/Ayushmaandotcom/Recongraph/actions/workflows/test.yml/badge.svg)](https://github.com/Ayushmaandotcom/Recongraph/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Version](https://img.shields.io/badge/version-0.9.0-blue)

**A deterministic, graph-based evidence reasoning framework for financial reconciliation.**

ReconGraph frames reconciliation as a formal reasoning problem. Instead of opaque scalar similarity scores, it builds a structured evidence graph, evaluates competing hypotheses, and routes decisions it cannot confidently resolve to human review.

## How It Works

1. **Records** — Purchase invoices and GST filings are ingested as typed domain objects.
2. **Blocking** — Records sharing common keys (reference, tax identity) are grouped into candidate pairs.
3. **Evidence Providers** — Five independent providers evaluate each pair: Financial (amount), Temporal (date proximity), Tax Identity, Vendor Name (fuzzy), and Reference (rarity-weighted).
4. **Hypothesis Evaluation** — Connected components are partitioned into hypotheses and scored under a configurable `RelationshipPolicy`.
5. **Decision Routing** — High-confidence matches are auto-approved. Weak or ambiguous matches produce `ReviewPacket` objects for human triage. **No record is ever silently dropped** (the conservation invariant is tested in CI).

## Quick Start

### Prerequisites

- Python 3.11+

### Installation

```bash
git clone https://github.com/Ayushmaandotcom/Recongraph.git
cd Recongraph
pip install -e ".[dev]"
```

### Running the Engine

See [`quickstart.py`](quickstart.py) for a complete, runnable example. This script is executed in CI on every push — if it fails, the docs are wrong.

```python
from datetime import date
from decimal import Decimal
from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider, TemporalEvidenceProvider,
    TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
)
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import (
    ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy
)

# Create records
purchase = PurchaseRecord(
    record_id="P-001", vendor_name="TechCorp Private Limited",
    reference="INV-2026-A", amount=Decimal("15000.00"),
    record_date=date(2026, 1, 15), tax_identity="07TECHC1234A1Z5",
)
gst = GSTRecord(
    record_id="G-001", vendor_name="TECHCORP PVT LTD",
    reference="INV-2026-A", amount=Decimal("15000.00"),
    record_date=date(2026, 1, 16), tax_identity="07TECHC1234A1Z5",
)

# Setup providers (see quickstart.py for full context setup)
# ...

result = ReconGraphEngine(ReconGraphConfig(), providers).reconcile([purchase], [gst])

if result.auto_matches:
    print("AUTO_MATCH:", result.auto_matches[0].rationale)
elif result.review_packets:
    print(f"REVIEW: {result.review_packets[0].checklist}")
```

### Running Tests

```bash
pytest tests/ -q
python quickstart.py
```

## ReconBench

ReconGraph ships with **ReconBench**, a built-in benchmark suite that generates synthetic invoice datasets and measures engine accuracy:

```bash
python -m recongraph.cli benchmark --size 100
```

Use `--faf` to enable the Failure Analysis Framework, which produces detailed forensic reports for every misclassification.

## Project Status

ReconGraph is at **v0.9.0**. The core engine (candidate generation, hypothesis evaluation, decision routing, conservation invariant) is stable and tested (690+ tests). Areas under active development:

- Bipolar evidence model (support vs. conflict)
- ReconBench expansion and real-world validation
- Interactive pipeline visualization

## Contributing

We welcome contributions. Please ensure `pytest tests/` and `python quickstart.py` both pass before submitting a PR.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
