import pytest
from recongraph.domain.claims import CoreClaims
from recongraph.domain.scopes import ScopeKind

def test_core_claim_ids_are_unique():
    # Extract all descriptors
    descriptors = [getattr(CoreClaims, k) for k in dir(CoreClaims) if not k.startswith("_") and k.isupper()]
    ids = [d.claim_id for d in descriptors]
    assert len(ids) == len(set(ids))

def test_core_claim_descriptors_are_unique():
    descriptors = [getattr(CoreClaims, k) for k in dir(CoreClaims) if not k.startswith("_") and k.isupper()]
    assert len(descriptors) == len(set(descriptors))

def test_core_claim_catalog_is_immutable():
    with pytest.raises(AttributeError):
        CoreClaims.NEW_CLAIM = "foo" # type: ignore

def test_same_gst_registration_is_distinct_from_same_legal_entity():
    assert CoreClaims.SAME_GST_REGISTRATION != CoreClaims.SAME_LEGAL_ENTITY

def test_lexical_name_similarity_is_distinct_from_legal_entity_identity():
    assert CoreClaims.LEXICAL_NAME_SIMILARITY != CoreClaims.SAME_LEGAL_ENTITY
