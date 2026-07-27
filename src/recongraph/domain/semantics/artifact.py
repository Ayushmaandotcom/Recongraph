import hashlib
import json
import struct
from dataclasses import dataclass
from typing import Tuple
from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest

@dataclass(frozen=True, slots=True, order=True)
class EmbeddingProviderIdentity:
    provider_id: str
    model_id: str
    semantic_version: str

@dataclass(frozen=True, slots=True, order=True)
class DerivedEmbeddingArtifactIdentity:
    digest: str
    
    @classmethod
    def compute(cls, raw_text: str, provider: EmbeddingProviderIdentity) -> "DerivedEmbeddingArtifactIdentity":
        payload = {
            "schema": "recongraph.embedding_artifact.v1",
            "raw_text": raw_text,
            "provider_id": provider.provider_id,
            "model_id": provider.model_id,
            "semantic_version": provider.semantic_version
        }
        canonical_bytes = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        
        digest_hex = hashlib.sha256(b"recongraph:embedding_artifact:v1\x00" + canonical_bytes).hexdigest()
        return cls(f"sha256:{digest_hex}")
        
    def to_kernel_identity_ref(self) -> KernelIdentityRef:
        return KernelIdentityRef(
            domain=IdentityDomainId("recongraph.embedding_artifact"),
            schema=IdentitySchemaId("recongraph.embedding_artifact.v1"),
            digest=IdentityDigest(self.digest)
        )

@dataclass(frozen=True)
class DerivedEmbeddingArtifact:
    """
    Materialized structure caching the float vector.
    Strictly tied to a specific provider and model version for K5 caching provenance.
    """
    provider_identity: EmbeddingProviderIdentity
    raw_text: str
    vector: Tuple[float, ...]
    
    @property
    def identity(self) -> DerivedEmbeddingArtifactIdentity:
        return DerivedEmbeddingArtifactIdentity.compute(self.raw_text, self.provider_identity)


class SimulatedEmbeddingProvider:
    """
    Deterministic simulated embedding provider for V1.
    Uses basic hashing and a predefined dictionary of concepts to output 384-dimensional vectors.
    """
    IDENTITY = EmbeddingProviderIdentity(
        provider_id="simulated",
        model_id="v1-deterministic-384",
        semantic_version="1.0.0"
    )
    
    # Simple semantic mapping for testing.
    # In reality, this would be an API call to OpenAI / Gemini.
    _SIMULATED_MAPPING = {
        "OFFICE SUPPLIES": "CONCEPT_OFFICE_SUPPLIES",
        "STATIONERY": "CONCEPT_OFFICE_SUPPLIES",
        "PENS": "CONCEPT_OFFICE_SUPPLIES",
        
        "LAPTOP": "CONCEPT_HARDWARE",
        "COMPUTER": "CONCEPT_HARDWARE",
        "HARDWARE": "CONCEPT_HARDWARE",
        
        "SOFTWARE": "CONCEPT_SOFTWARE",
        "AWS": "CONCEPT_SOFTWARE",
        "CLOUD": "CONCEPT_SOFTWARE",
        
        "CONSULTING": "CONCEPT_SERVICES",
        "SERVICES": "CONCEPT_SERVICES",
        "PLUMBING": "CONCEPT_SERVICES_PLUMBING"
    }

    @classmethod
    def _generate_deterministic_vector(cls, seed: str) -> Tuple[float, ...]:
        import random
        # Seed random with a hash to guarantee deterministic floats
        h = hashlib.sha256(seed.encode('utf-8')).hexdigest()
        random.seed(h)
        vec = [random.gauss(0, 1) for _ in range(384)]
        # L2 normalize
        norm = sum(x**2 for x in vec) ** 0.5
        return tuple(x / norm for x in vec)

    @classmethod
    def embed(cls, text: str) -> DerivedEmbeddingArtifact:
        # Normalize text for mapping
        import re
        norm_text = re.sub(r"[^\w\s]", "", text).upper().strip()
        
        # If it matches our dictionary, use the mapped concept as the seed, else use the norm_text.
        # This simulates high cosine similarity for known synonyms.
        concept_seed = cls._SIMULATED_MAPPING.get(norm_text, norm_text)
        
        vector = cls._generate_deterministic_vector(concept_seed)
        
        return DerivedEmbeddingArtifact(
            provider_identity=cls.IDENTITY,
            raw_text=text,
            vector=vector
        )
