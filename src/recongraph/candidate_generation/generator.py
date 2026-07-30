from dataclasses import dataclass
from typing import Iterable, Sequence, Any
from recongraph.candidate_generation.blockers import Blocker
from recongraph.candidate_generation.index import InvertedIndex
from recongraph.domain.records import PurchaseRecord, GSTRecord

@dataclass(frozen=True)
class CandidateEdge:
    """
    Represents a plausible pairing between a purchase and GST record,
    along with the exact keys that connected them.
    """
    purchase: PurchaseRecord
    gst_record: GSTRecord
    shared_blocking_keys: frozenset[str]

from recongraph.plugins.provider import EvidenceProvider
from recongraph.plugins.provider_v2 import EvidenceProviderV2

class CandidateGenerator:
    """
    Orchestrates the blocking and indexing strategy to yield CandidateEdges
    in sub-quadratic time by eliminating records with disjoint blocking keys.
    """
    def __init__(self, providers: Iterable[EvidenceProvider | EvidenceProviderV2]):
        blockers: list[Any] = []
        for provider in providers:
            blockers.extend(provider.get_blockers())
        self.blockers = tuple(blockers)
        
    def generate(
        self,
        purchases: Iterable[PurchaseRecord],
        gst_records: Iterable[GSTRecord],
    ) -> Iterable[CandidateEdge]:
        """
        Yields edges where the purchase and GST record share at least one blocking key.
        """
        # Build index for the larger/stationary set (we assume GST records are the corpus)
        gst_index = InvertedIndex(self.blockers)
        for gst in gst_records:
            gst_index.add(gst)
            
        # Probe the index with purchases
        for purchase in purchases:
            purchase_keys = set()
            for blocker in self.blockers:
                purchase_keys.update(blocker.extract_keys(purchase))
                
            if not purchase_keys:
                continue
                
            # Aggregate matches: GSTRecord -> shared_keys
            matches = {}  # type: ignore
            for key in sorted(purchase_keys):
                for gst in gst_index.query(key):
                    if gst not in matches:
                        matches[gst] = set()
                    matches[gst].add(key)
                    
            # Yield candidate edges in deterministic order
            for gst, shared_keys in sorted(matches.items(), key=lambda item: item[0].record_id):
                yield CandidateEdge(
                    purchase=purchase,
                    gst_record=gst,
                    shared_blocking_keys=frozenset(shared_keys)
                )
