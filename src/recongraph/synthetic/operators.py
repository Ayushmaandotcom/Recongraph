from typing import Protocol, TypeVar
import dataclasses
from recongraph.domain.records import PurchaseRecord, GSTRecord

TRecord = TypeVar('TRecord', PurchaseRecord, GSTRecord)

class MutationOperator(Protocol):
    """A pure function that applies noise or structural changes to a domain record."""
    def apply(self, record: TRecord) -> TRecord:
        ...

class VendorMutationOperator:
    """Applies vendor name mutations (e.g., 'ABC Pvt Ltd' -> 'ABC Private Limited')."""
    def __init__(self, new_vendor_name: str):
        self.new_vendor_name = new_vendor_name

    def apply(self, record: TRecord) -> TRecord:
        return dataclasses.replace(record, vendor_name=self.new_vendor_name)

class ReferenceMutationOperator:
    """Applies reference mutations (e.g., dropping hyphens, OCR noise)."""
    def __init__(self, new_reference: str | None):
        self.new_reference = new_reference

    def apply(self, record: TRecord) -> TRecord:
        return dataclasses.replace(record, reference=self.new_reference)

class AmountMutationOperator:
    """Modifies the financial amount (e.g., for split payments or errors)."""
    def __init__(self, new_amount: float):
        self.new_amount = new_amount

    def apply(self, record: TRecord) -> TRecord:
        return dataclasses.replace(record, amount=self.new_amount)
