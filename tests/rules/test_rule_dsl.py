import pytest
from recongraph.rules.models import RuleSet, Rule, RuleViolation
from recongraph.rules.dsl import parse_rule

def test_parse_simple_rule():
    rule_str = "REQUIRE tax_identity_match WHEN amount_difference > 0"
    rule = parse_rule("rule-1", "Test Rule", rule_str)
    
    assert rule.rule_id == "rule-1"
    assert rule.condition_ast["type"] == "REQUIRE"
    assert rule.condition_ast["target"] == "tax_identity_match"
    assert rule.condition_ast["when"]["left"] == "amount_difference"
    assert rule.condition_ast["when"]["operator"] == ">"
    assert rule.condition_ast["when"]["right"] == 0

def test_parse_block_rule():
    rule_str = "BLOCK IF vendor_name_conflict AND missing_reference"
    rule = parse_rule("rule-2", "Block Rule", rule_str)
    
    assert rule.condition_ast["type"] == "BLOCK"
    assert rule.condition_ast["if"]["type"] == "AND"
    assert rule.condition_ast["if"]["conditions"][0] == "vendor_name_conflict"
    assert rule.condition_ast["if"]["conditions"][1] == "missing_reference"
