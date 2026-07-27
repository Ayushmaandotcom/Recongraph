from datetime import date
from decimal import Decimal
from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionMode
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.core_providers import FinancialEvidenceProvider, AmountMultipleEvidenceProvider AmountMultipleEvidenceProvider, AmountMultipleEvidenceProvider,

config = ReconGraphConfig(decision_config=DecisionConfig(decision_mode=DecisionMode.FUSION))
engine = ReconGraphEngine(config=config, providers=[FinancialEvidenceProvider(), AmountMultipleEvidenceProvider()])

p = PurchaseRecord(record_id="P1", vendor_name="Vendor A", reference="123", amount=Decimal("100"), record_date=date(2023, 1, 1), tax_identity="T1")
g = GSTRecord(record_id="G1", vendor_name="Vendor A", reference="123", amount=Decimal("100"), record_date=date(2023, 1, 1), tax_identity="T1")

result = engine.reconcile([p], [g])
print("Auto matches:", len(result.auto_matches))
