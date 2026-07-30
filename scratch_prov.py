from recongraph.plugins.core_providers import VendorEvidenceProvider
from recongraph.domain.records import PurchaseRecord, GSTRecord
from decimal import Decimal
from datetime import date

p = PurchaseRecord(record_id="P1", vendor_name="Acme Corp", tax_identity="GST123", reference=None, amount=Decimal("100"), record_date=date(2023,1,1))
g = GSTRecord(record_id="G1", vendor_name="Acme Corp", tax_identity="GST123", reference=None, amount=Decimal("100"), record_date=date(2023,1,1))

prov = VendorEvidenceProvider()
contrib = prov.evaluate([p], [g])
print(f"Contrib Metadata: {contrib.metadata}")
