from dataclasses import dataclass
from typing import Optional

from recongraph.contrib.kernel.derivations import (
    DerivedArtifactIdentity,
    DerivedArtifactTypeId,
    CanonicalPayloadEnvelope
)
from recongraph.domain.tax.parser import ParsedTaxIdentifierArtifact

@dataclass(frozen=True)
class TaxIdentifierArtifact:
    """
    Immutable, identity-bearing semantic artifact for a tax identifier.
    Guarantees deterministic identity hashing based strictly on extracted semantics.
    """
    parsed_result: ParsedTaxIdentifierArtifact
    identity: DerivedArtifactIdentity
    
    @classmethod
    def create(cls, parsed: ParsedTaxIdentifierArtifact) -> 'TaxIdentifierArtifact':
        # The semantic meaning is defined by the valid PAN or GSTIN.
        # Invalid or uninterpretable strings have no semantic payload, 
        # so they share a deterministic "null" identity.
        
        payload_dict = {}
        if parsed.gstin_valid:
            payload_dict["gstin"] = parsed.gstin_candidate
        if parsed.pan_valid:
            payload_dict["pan"] = parsed.pan_candidate
            
        payload = CanonicalPayloadEnvelope(payload_dict)
        
        identity = DerivedArtifactIdentity.compute(
            type_id=DerivedArtifactTypeId("recongraph.tax_identifier.v1"),
            semantic_version="1.0.0",
            payload=payload
        )
        
        return cls(
            parsed_result=parsed,
            identity=identity
        )

from decimal import Decimal

@dataclass(frozen=True)
class TaxIntelligenceArtifact:
    """
    Combines tax identity semantics with financial intelligence (rates, amounts)
    for tax intelligence reasoning.
    """
    tax_identity: TaxIdentifierArtifact
    amount: Decimal
    net_amount: Decimal | None
    tax_amount: Decimal | None
    tax_rate: Decimal | None

    @classmethod
    def create(
        cls, 
        parsed: ParsedTaxIdentifierArtifact,
        amount: Decimal,
        net_amount: Decimal | None,
        tax_amount: Decimal | None,
        tax_rate: Decimal | None
    ) -> 'TaxIntelligenceArtifact':
        return cls(
            tax_identity=TaxIdentifierArtifact.create(parsed),
            amount=amount,
            net_amount=net_amount,
            tax_amount=tax_amount,
            tax_rate=tax_rate
        )
