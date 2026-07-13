import pytest
from recongraph.domain.observations import ObservationState, InterpretationState

# Testing orthogonal state algebra conceptually

def test_present_can_coexist_with_interpreted():
    # Example: Valid vendor name, parsed successfully.
    # In a future EvidenceAssertion, we might see:
    assert ObservationState.PRESENT == "present"
    assert InterpretationState.INTERPRETED == "interpreted"

def test_present_can_coexist_with_uninterpretable():
    # Example: "UNKNOWN" literal or Japanese string in English parser.
    assert ObservationState.PRESENT == "present"
    assert InterpretationState.UNINTERPRETABLE == "uninterpretable"

def test_invalid_can_coexist_with_interpreted():
    # Example: GSTIN="BANANA" -> document.contains_invalid_tax_identifier is evaluated true.
    assert ObservationState.INVALID == "invalid"
    assert InterpretationState.INTERPRETED == "interpreted"

def test_invalid_can_coexist_with_uninterpretable():
    # Example: Malformed amount string in a math evaluator.
    assert ObservationState.INVALID == "invalid"
    assert InterpretationState.UNINTERPRETABLE == "uninterpretable"

def test_observation_state_does_not_determine_interpretation_state():
    # Both outcomes are possible for a PRESENT observation
    present_interpreted = InterpretationState.INTERPRETED
    present_uninterpretable = InterpretationState.UNINTERPRETABLE
    assert present_interpreted != present_uninterpretable

def test_interpretation_state_does_not_determine_observation_state():
    # Both outcomes are possible for an INTERPRETED state
    interpreted_present = ObservationState.PRESENT
    interpreted_invalid = ObservationState.INVALID
    assert interpreted_present != interpreted_invalid

def test_partial_interpretation_state_does_not_exist():
    states = [s.value for s in InterpretationState]
    assert "partially_interpreted" not in states
    assert len(states) == 2
