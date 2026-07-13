import pytest
from recongraph.synthetic.builder import DatasetBuilder
from recongraph.synthetic.canonical import get_hn001_exact_match, get_hn004_rare_reference_overrides_amount

def test_dataset_builder_hn001():
    spec = get_hn001_exact_match()
    builder = DatasetBuilder()
    
    dataset = builder.build_from_specs([spec], "DATASET_HN001")
    
    assert dataset.dataset_id == "DATASET_HN001"
    assert len(dataset.purchases) == 1
    assert len(dataset.gsts) == 1
    assert len(dataset.expected_outcomes) == 1
    
    # Assert unmodified base values
    assert dataset.purchases[0].amount == 100.0
    assert dataset.gsts[0].amount == 100.0

def test_dataset_builder_hn004_with_mutation():
    spec = get_hn004_rare_reference_overrides_amount()
    builder = DatasetBuilder()
    
    dataset = builder.build_from_specs([spec], "DATASET_HN004")
    
    assert len(dataset.purchases) == 1
    assert len(dataset.gsts) == 1
    
    # Assert mutation operator successfully applied
    assert dataset.purchases[0].amount == 100.0
    assert dataset.gsts[0].amount == 99.0
