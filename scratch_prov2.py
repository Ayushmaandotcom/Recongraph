from recongraph.domain.records import PurchaseRecord, GSTRecord
from decimal import Decimal
from datetime import date
from recongraph.config import ReconGraphConfig
from recongraph.engine import ReconGraphEngine
from recongraph.plugins.core_providers import VendorEvidenceProvider

p = PurchaseRecord(record_id="P1", vendor_name="Acme Corp", tax_identity="GST123", reference=None, amount=Decimal("100"), record_date=date(2023,1,1))
g = GSTRecord(record_id="G1", vendor_name="Acme Corp", tax_identity="GST123", reference=None, amount=Decimal("100"), record_date=date(2023,1,1))

config = ReconGraphConfig.default()
# Find vendor provider
for prov in config.evidence_providers:
    if isinstance(prov, VendorEvidenceProvider):
        contrib = prov.evaluate([p], [g])
        print(f"Vendor Contrib Metadata: {contrib.metadata}")

    if prov.get_name() == "temporal":
        contrib = prov.evaluate([p], [g])
        print(f"Temporal Contrib Metadata: {contrib.metadata}")
