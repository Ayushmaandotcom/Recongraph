import pytest
from datetime import date
from decimal import Decimal

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.domain.document.layout import DocumentLayoutArtifact, DocumentBlock, DocumentRegion, BoundingBox
from recongraph.plugins.core_providers import DocumentIntelligenceProvider

from typing import Optional
def create_mock_purchase(layout: Optional[DocumentLayoutArtifact] = None) -> PurchaseRecord:
    return PurchaseRecord(
        record_id="p1", vendor_name="Acme", reference="1", 
        amount=Decimal("100"), record_date=date(2023,1,1),
        tax_identity=None, net_amount=None, tax_amount=None, tax_rate=None,
        layout_artifact=layout
    )

def create_mock_gst() -> GSTRecord:
    return GSTRecord(
        record_id="g1", vendor_name="Acme", reference="1", 
        amount=Decimal("100"), record_date=date(2023,1,1),
        tax_identity=None, net_amount=None, tax_amount=None, tax_rate=None,
        layout_artifact=None
    )

def test_document_intelligence_provider_with_signature():
    provider = DocumentIntelligenceProvider()
    
    layout = DocumentLayoutArtifact(
        blocks=(
            DocumentBlock(
                region_type=DocumentRegion.SIGNATURE,
                box=BoundingBox(0, 0, 100, 100, 1)
            ),
        )
    )
    
    p = create_mock_purchase(layout)
    g = create_mock_gst()
    
    contrib = provider.evaluate([p], [g])
    
    assertions = contrib.metadata.get("assertions", tuple())
    assert len(assertions) == 1
    
    a1 = assertions[0]
    assert a1.proposition.claim.claim_id.value == "document.has_valid_signature_region"
    assert a1.polarity.value == "support"

def test_document_intelligence_provider_with_totals_and_header():
    provider = DocumentIntelligenceProvider()
    
    layout = DocumentLayoutArtifact(
        blocks=(
            DocumentBlock(
                region_type=DocumentRegion.HEADER,
                box=BoundingBox(0, 0, 100, 20, 1)
            ),
            DocumentBlock(
                region_type=DocumentRegion.TOTALS_BLOCK,
                box=BoundingBox(0, 80, 100, 100, 1)
            ),
        )
    )
    
    p = create_mock_purchase(layout)
    g = create_mock_gst()
    
    contrib = provider.evaluate([p], [g])
    
    assertions = contrib.metadata.get("assertions", tuple())
    assert len(assertions) == 2
    
    claims = {a.proposition.claim.claim_id.value for a in assertions}
    assert "document.totals_block_consistency" in claims
    assert "document.header_match" in claims

def test_document_intelligence_provider_no_layout():
    provider = DocumentIntelligenceProvider()
    
    p = create_mock_purchase()
    g = create_mock_gst()
    
    contrib = provider.evaluate([p], [g])
    assertions = contrib.metadata.get("assertions", tuple())
    
    assert len(assertions) == 0
