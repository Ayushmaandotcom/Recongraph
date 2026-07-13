import pytest
from decimal import Decimal
from recongraph.domain.scopes import SubjectRef
from recongraph.domain.observations import (
    FieldPath,
    ObservationSlot,
    ObservationState,
    Observation,
    ObservationIdentity
)

def test_field_path_grammar():
    assert FieldPath("vendor_name").value == "vendor_name"
    assert FieldPath("document.header.vendor").value == "document.header.vendor"

    with pytest.raises(ValueError):
        FieldPath("VendorName")
    with pytest.raises(ValueError):
        FieldPath(".vendor_name")
    with pytest.raises(ValueError):
        FieldPath("vendor_name.")
    with pytest.raises(ValueError):
        FieldPath("vendor..name")
    with pytest.raises(ValueError):
        FieldPath("vendor-name")
    with pytest.raises(ValueError):
        FieldPath("vendor name")
    with pytest.raises(ValueError):
        FieldPath("vendor[0]")
    with pytest.raises(ValueError):
        FieldPath("")

@pytest.fixture
def base_slot():
    return ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor_name"))

def test_slot_stability_across_value_changes(base_slot):
    # KOM-001
    o1 = Observation.create(base_slot, ObservationState.PRESENT, "ABC")
    o2 = Observation.create(base_slot, ObservationState.PRESENT, "XYZ")
    assert o1.identity.slot == o2.identity.slot

def test_revision_distinction(base_slot):
    # KOM-002
    o1 = Observation.create(base_slot, ObservationState.PRESENT, "ABC")
    o2 = Observation.create(base_slot, ObservationState.PRESENT, "XYZ")
    assert o1.identity != o2.identity

def test_exact_reconstruction(base_slot):
    # KOM-003, ODUP001, ODUP005, ODUP008
    o1 = Observation.create(base_slot, ObservationState.PRESENT, "ABC")
    o2 = Observation.create(base_slot, ObservationState.PRESENT, "ABC")
    assert o1.identity == o2.identity

def test_subject_distinction():
    # KOM-004
    s1 = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    s2 = ObservationSlot(SubjectRef("urn:2"), FieldPath("vendor"))
    o1 = Observation.create(s1, ObservationState.PRESENT, "ABC")
    o2 = Observation.create(s2, ObservationState.PRESENT, "ABC")
    assert o1.identity.slot != o2.identity.slot
    assert o1.identity != o2.identity

def test_field_distinction(base_slot):
    # KOM-005, ODUP002
    s1 = base_slot
    s2 = ObservationSlot(SubjectRef("urn:1"), FieldPath("name"))
    o1 = Observation.create(s1, ObservationState.PRESENT, "ABC")
    o2 = Observation.create(s2, ObservationState.PRESENT, "ABC")
    assert o1.identity.slot != o2.identity.slot
    assert o1.identity != o2.identity

def test_state_distinction(base_slot):
    # KOM-006, ODUP004
    o1 = Observation.create(base_slot, ObservationState.PRESENT, "ABC")
    o2 = Observation.create(base_slot, ObservationState.INVALID, "ABC")
    assert o1.identity != o2.identity

def test_missing_determinism(base_slot):
    # KOM-007, ODUP010
    o1 = Observation.create(base_slot, ObservationState.MISSING, None)
    o2 = Observation.create(base_slot, ObservationState.MISSING, None)
    assert o1.identity == o2.identity

def test_runtime_object_independence(base_slot):
    # KOM-008
    val1 = "".join(["A", "B", "C"])
    val2 = "".join(["A", "B", "C"])
    o1 = Observation.create(base_slot, ObservationState.PRESENT, val1)
    o2 = Observation.create(base_slot, ObservationState.PRESENT, val2)
    assert o1.identity == o2.identity

def test_type_preservation(base_slot):
    # KOM-009
    o1 = Observation.create(base_slot, ObservationState.PRESENT, 1)
    o2 = Observation.create(base_slot, ObservationState.PRESENT, 1.0)
    assert o1.identity != o2.identity

def test_invalid_value_preservation(base_slot):
    # KOM-015
    o1 = Observation.create(base_slot, ObservationState.INVALID, "ABC")
    o2 = Observation.create(base_slot, ObservationState.INVALID, "XYZ")
    assert o1.identity != o2.identity

def test_empty_string_handling(base_slot):
    # KOM-016
    o1 = Observation.create(base_slot, ObservationState.PRESENT, "")
    o2 = Observation.create(base_slot, ObservationState.MISSING, None)
    assert o1.identity != o2.identity

def test_whitespace_sensitivity(base_slot):
    # KOM-017
    o1 = Observation.create(base_slot, ObservationState.PRESENT, "ABC")
    o2 = Observation.create(base_slot, ObservationState.PRESENT, " ABC ")
    assert o1.identity != o2.identity

def test_decimal_stability(base_slot):
    # KOM-018
    o1 = Observation.create(base_slot, ObservationState.PRESENT, Decimal("1.0"))
    o2 = Observation.create(base_slot, ObservationState.PRESENT, Decimal("1.0"))
    o3 = Observation.create(base_slot, ObservationState.PRESENT, Decimal("1.00"))
    assert o1.identity == o2.identity
    assert o1.identity != o3.identity

def test_boolean_integer_distinction(base_slot):
    # KOM-019
    o1 = Observation.create(base_slot, ObservationState.PRESENT, True)
    o2 = Observation.create(base_slot, ObservationState.PRESENT, 1)
    assert o1.identity != o2.identity

def test_missing_value_check(base_slot):
    # KOM-020
    with pytest.raises(ValueError):
        Observation.create(base_slot, ObservationState.MISSING, "ABC")

def test_present_requires_value(base_slot):
    with pytest.raises(ValueError):
        Observation.create(base_slot, ObservationState.PRESENT, None)

def test_invalid_requires_value(base_slot):
    with pytest.raises(ValueError):
        Observation.create(base_slot, ObservationState.INVALID, None)

def test_serialization_stability(base_slot):
    # KOM-014
    import json
    o1 = Observation.create(base_slot, ObservationState.PRESENT, "ABC")
    o2 = Observation.create(base_slot, ObservationState.PRESENT, "ABC")
    j1 = json.dumps(o1.to_dict(), sort_keys=True)
    j2 = json.dumps(o2.to_dict(), sort_keys=True)
    assert j1 == j2

def test_reject_nonfinite_floats(base_slot):
    with pytest.raises(ValueError):
        Observation.create(base_slot, ObservationState.PRESENT, float('inf'))
    with pytest.raises(ValueError):
        Observation.create(base_slot, ObservationState.PRESENT, float('nan'))

def test_observation_identity_is_consistent():
    # Attempting to lie about identity fails
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    o1 = Observation.create(slot, ObservationState.PRESENT, "ABC")
    with pytest.raises(ValueError):
        Observation(identity=o1.identity, state=ObservationState.PRESENT, value="XYZ")
