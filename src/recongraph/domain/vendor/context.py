import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional
from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
from recongraph.domain.vendor.corpus import VendorCorpusProfile
from recongraph.domain.vendor.knowledge import OrganizationalKnowledgeBase

@dataclass(frozen=True, slots=True, order=True)
class VendorIdentityContextIdentity:
    """Deterministic K6 identity for VendorIdentityContext."""
    digest: str

    @classmethod
    def compute(
        cls,
        corpus_profile_digest: Optional[str],
        knowledge_base_digest: str,
        interpreter_policy_version: str,
        fuzzy_minimum_length: int,
        fuzzy_threshold: float,
        distinctiveness_threshold: float
    ) -> "VendorIdentityContextIdentity":
        
        payload = {
            "schema": "recongraph.vendor_identity_context.v1",
            "corpus_profile_digest": corpus_profile_digest,
            "knowledge_base_digest": knowledge_base_digest,
            "interpreter_policy_version": interpreter_policy_version,
            "fuzzy_minimum_length": fuzzy_minimum_length,
            "fuzzy_threshold": fuzzy_threshold,
            "distinctiveness_threshold": distinctiveness_threshold
        }
        
        canonical_bytes = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False
        ).encode("utf-8")
        
        domain_separated = b"recongraph:vendor_identity_context:v1\x00" + canonical_bytes
        digest_hex = hashlib.sha256(domain_separated).hexdigest()
        return cls(f"sha256:{digest_hex}")

    def to_kernel_identity_ref(self) -> KernelIdentityRef:
        return KernelIdentityRef(
            domain=IdentityDomainId("recongraph.vendor_identity_context"),
            schema=IdentitySchemaId("recongraph.vendor_identity_context.v1"),
            digest=IdentityDigest(self.digest)
        )


@dataclass(frozen=True)
class VendorIdentityContext:
    corpus_profile: Optional[VendorCorpusProfile]
    knowledge_base: OrganizationalKnowledgeBase = field(default_factory=OrganizationalKnowledgeBase.empty)
    interpreter_policy_version: str = "1.0.0"
    fuzzy_minimum_length: int = 6
    fuzzy_threshold: float = 0.85
    distinctiveness_threshold: float = 0.01
    
    @property
    def identity(self) -> VendorIdentityContextIdentity:
        return VendorIdentityContextIdentity.compute(
            corpus_profile_digest=self.corpus_profile.digest if self.corpus_profile else None,
            knowledge_base_digest=self.knowledge_base.compute_digest(),
            interpreter_policy_version=self.interpreter_policy_version,
            fuzzy_minimum_length=self.fuzzy_minimum_length,
            fuzzy_threshold=self.fuzzy_threshold,
            distinctiveness_threshold=self.distinctiveness_threshold
        )
