import pytest
import json
from recongraph.domain.claims import ClaimDescriptor, ClaimSymmetry
from recongraph.domain.scopes import ScopeKind, SubjectRef, PropositionSubject

@pytest.fixture
def sym_descriptor():
    return ClaimDescriptor(
        claim_id="identity.same",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR, ScopeKind.GROUP_PAIR}
    )

@pytest.fixture
def dir_descriptor():
    return ClaimDescriptor(
        claim_id="document.supersedes",
        semantic_version=1,
        symmetry=ClaimSymmetry.DIRECTIONAL,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR}
    )

def test_scope_kind_values_are_stable():
    assert ScopeKind.RECORD_PAIR.value == "record_pair"

def test_subject_ref_is_value_based():
    s1 = SubjectRef("urn:1")
    s2 = SubjectRef("urn:1")
    assert s1 == s2
    assert hash(s1) == hash(s2)

def test_subject_ref_order_is_deterministic_if_ordering_is_supported():
    s1 = SubjectRef("urn:1")
    s2 = SubjectRef("urn:2")
    assert s1 < s2

def test_subject_ref_serializes_stable_identity():
    assert SubjectRef("urn:1").to_dict() == {"urn": "urn:1"}

def test_empty_scope(sym_descriptor):
    with pytest.raises(ValueError, match="SC-001 Violation"):
        PropositionSubject.create(sym_descriptor, ScopeKind.RECORD_PAIR, [], [])

def test_record_scope_with_two_subjects(sym_descriptor):
    rec_desc = ClaimDescriptor("a.b", 1, ClaimSymmetry.SYMMETRIC, {ScopeKind.RECORD})
    with pytest.raises(ValueError, match="SC-002 Violation"):
        PropositionSubject.create(rec_desc, ScopeKind.RECORD, [SubjectRef("urn:1")], [SubjectRef("urn:2")])

def test_pair_scope_with_empty_left(sym_descriptor):
    with pytest.raises(ValueError, match="SC-002 Violation"):
        PropositionSubject.create(sym_descriptor, ScopeKind.RECORD_PAIR, [], [SubjectRef("urn:1")])

def test_pair_scope_with_empty_right(sym_descriptor):
    with pytest.raises(ValueError, match="SC-002 Violation"):
        PropositionSubject.create(sym_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("urn:1")], [])

def test_pair_scope_with_two_left_subjects(sym_descriptor):
    with pytest.raises(ValueError, match="SC-002 Violation"):
        PropositionSubject.create(sym_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("urn:1"), SubjectRef("urn:2")], [SubjectRef("urn:3")])

def test_duplicate_left_subject(sym_descriptor):
    with pytest.raises(ValueError, match="SC-003 Violation"):
        PropositionSubject.create(sym_descriptor, ScopeKind.GROUP_PAIR, [SubjectRef("urn:1"), SubjectRef("urn:1")], [SubjectRef("urn:2"), SubjectRef("urn:3")])

def test_group_pair_with_singleton_singleton(sym_descriptor):
    with pytest.raises(ValueError, match="SC-002 Violation"):
        PropositionSubject.create(sym_descriptor, ScopeKind.GROUP_PAIR, [SubjectRef("urn:1")], [SubjectRef("urn:2")])

def test_undeclared_scope_kind_for_claim():
    d = ClaimDescriptor("a.b", 1, ClaimSymmetry.SYMMETRIC, {ScopeKind.RECORD})
    with pytest.raises(ValueError, match="SC-008 Violation"):
        PropositionSubject.create(d, ScopeKind.RECORD_PAIR, [SubjectRef("urn:1")], [SubjectRef("urn:2")])

# Metamorphic Tests

def test_symmetric_scope_reversal(sym_descriptor):
    # A <-> B should equal B <-> A
    s1 = PropositionSubject.create(sym_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("urn:A")], [SubjectRef("urn:B")])
    s2 = PropositionSubject.create(sym_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("urn:B")], [SubjectRef("urn:A")])
    assert s1 == s2
    assert hash(s1) == hash(s2)

def test_directional_scope_reversal(dir_descriptor):
    # A -> B should NOT equal B -> A
    s1 = PropositionSubject.create(dir_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("urn:A")], [SubjectRef("urn:B")])
    s2 = PropositionSubject.create(dir_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("urn:B")], [SubjectRef("urn:A")])
    assert s1 != s2
    assert hash(s1) != hash(s2)

def test_intra_side_permutation(sym_descriptor):
    # {A, B, C} <-> {D} should equal {C, A, B} <-> {D}
    s1 = PropositionSubject.create(sym_descriptor, ScopeKind.GROUP_PAIR, [SubjectRef("A"), SubjectRef("B"), SubjectRef("C")], [SubjectRef("D")])
    s2 = PropositionSubject.create(sym_descriptor, ScopeKind.GROUP_PAIR, [SubjectRef("C"), SubjectRef("A"), SubjectRef("B")], [SubjectRef("D")])
    assert s1 == s2

def test_scope_distinction_pair_vs_group(sym_descriptor):
    s1 = PropositionSubject.create(sym_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("P1")], [SubjectRef("G1")])
    s2 = PropositionSubject.create(sym_descriptor, ScopeKind.GROUP_PAIR, [SubjectRef("P1")], [SubjectRef("G1"), SubjectRef("G2")])
    assert s1 != s2

def test_overlap_non_identity(sym_descriptor):
    s1 = PropositionSubject.create(sym_descriptor, ScopeKind.GROUP_PAIR, [SubjectRef("P1"), SubjectRef("P2")], [SubjectRef("G1")])
    s2 = PropositionSubject.create(sym_descriptor, ScopeKind.GROUP_PAIR, [SubjectRef("P2"), SubjectRef("P3")], [SubjectRef("G1")])
    assert s1 != s2

def test_scope_serialization_is_deterministic(sym_descriptor):
    s1 = PropositionSubject.create(sym_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("urn:A")], [SubjectRef("urn:B")])
    s2 = PropositionSubject.create(sym_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("urn:B")], [SubjectRef("urn:A")])
    # They should produce exactly the same JSON string when keys are sorted
    json1 = json.dumps(s1.to_dict(), sort_keys=True)
    json2 = json.dumps(s2.to_dict(), sort_keys=True)
    assert json1 == json2

def test_reversed_directional_scope_serializes_differently(dir_descriptor):
    s1 = PropositionSubject.create(dir_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("urn:A")], [SubjectRef("urn:B")])
    s2 = PropositionSubject.create(dir_descriptor, ScopeKind.RECORD_PAIR, [SubjectRef("urn:B")], [SubjectRef("urn:A")])
    json1 = json.dumps(s1.to_dict(), sort_keys=True)
    json2 = json.dumps(s2.to_dict(), sort_keys=True)
    assert json1 != json2
