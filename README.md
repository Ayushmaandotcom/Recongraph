# Recongraph

[![Tests](https://github.com/Ayushmaandotcom/Recongraph/actions/workflows/verify.yml/badge.svg)](https://github.com/Ayushmaandotcom/Recongraph/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A deterministic, graph-based evidence reasoning framework for financial reconciliation.**

Recongraph is an approach to financial reconciliation that moves beyond opaque scalar similarity scores. Instead of relying on rigid heuristic rules, Recongraph frames reconciliation as a formal reasoning problem, building a semantic graph of evidence.

## 🌟 Why Recongraph?

Traditional reconciliation systems fail at scale because they conflate *similarity* with *identity*. Recongraph extracts the structural semantic reality of records, distinguishing between "missing evidence" and "contradicting evidence".

- **Epistemic Honesty:** Missing evidence is never treated as a contradiction.
- **Decision Engine:** It evaluates Vendor, Tax, Financial, Reference, and Temporal evidence streams.
- **Explainability:** The engine yields an `ExplanationArtifact` outlining exactly which signals corroborated or contradicted a match.

## 🏗 Architecture at a Glance

1. **Observations:** Raw financial records (Purchases, GST, Bank lines) are ingested.
2. **Contributions:** Providers evaluate evidence and return structured contributions.
3. **Graph Building:** Records sharing blocking keys are connected in a Candidate Graph.
4. **Hypothesis Evaluation:** Connected components are partitioned into hypotheses and scored.
5. **Decision & Routing:** Sparse or conflicting matches are routed to manual review packets.

*(See [docs/architecture.md](docs/architecture.md) for system flows).*

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- `pip` or `uv`

### Installation

```bash
git clone https://github.com/Ayushmaandotcom/Recongraph.git
cd Recongraph

# Install the engine and its dependencies
pip install -e .
```

### Running the Engine (Example)

```python
from datetime import date
from decimal import Decimal
from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionMode
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.core_providers import (
    VendorEvidenceProvider,
    ReferenceEvidenceProvider,
    FinancialEvidenceProvider,
    TemporalEvidenceProvider,
    TaxEvidenceProvider
)
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy

# 1. Setup Providers
vendor_context = VendorIdentityContext(
    corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest='1'),
    interpreter_policy_version='1.0.0',
    fuzzy_minimum_length=6,
    fuzzy_threshold=0.85,
    distinctiveness_threshold=0.01
)
reference_context = ReferenceEvidenceContext(
    profile=ReferenceCorpusProfile(
        reference_count=1, 
        normalized_reference_frequency={"inv2026a": 1}, 
        numeric_token_document_frequency={"2026": 1}
    ),
    policy=ReferenceEvidencePolicy()
)
providers = [
    VendorEvidenceProvider(vendor_context),
    ReferenceEvidenceProvider(reference_context),
    FinancialEvidenceProvider(tolerance=0.05),
    TemporalEvidenceProvider(max_days=7),
    TaxEvidenceProvider()
]

# 2. Initialize Engine
config = ReconGraphConfig(decision_config=DecisionConfig(decision_mode=DecisionMode.FUSION))
engine = ReconGraphEngine(config=config, providers=providers)

# 3. Define Evidence
purchase = PurchaseRecord(
    record_id="P-001",
    vendor_name="TechCorp Private Limited",
    reference="INV-2026-A",
    amount=Decimal("15000.00"),
    record_date=date(2026, 1, 15),
    tax_identity="07ABCDE1234F1Z1"
)

gst = GSTRecord(
    record_id="G-001",
    vendor_name="TECHCORP PVT LTD",
    reference="2026-A",
    amount=Decimal("15000.00"),
    record_date=date(2026, 1, 16),
    tax_identity="07ABCDE1234F1Z1"
)

# 4. Evaluate Match
result = engine.reconcile([purchase], [gst])

if result.auto_matches:
    print(f"Action: {result.auto_matches[0].action.value}")
elif result.review_packets:
    packet = result.review_packets[0]
    print(f"Action: {packet.action.value}")
    if packet.explanation:
        print(f"Explanation: {packet.explanation.executive_summary['decision']}")
```

## 📖 Documentation

Dive deeper into ReconGraph's design philosophy and internal APIs:

- [API Reference](docs/api.md)
- [Architecture & Diagrams](docs/architecture.md)

## 🤝 Contributing

We welcome contributions! Please ensure your code passes our verification workflow before submitting.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
