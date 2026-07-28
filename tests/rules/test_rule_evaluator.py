import pytest
from recongraph.rules.models import RuleSet, Rule, RuleViolation
from recongraph.rules.evaluator import RuleEvaluator

def test_rule_evaluator():
    # Setup mock rule
    rule = Rule(
        rule_id="R001",
        description="Block if vendor conflict",
        condition_ast={"type": "BLOCK", "if": {"type": "AND", "conditions": ["vendor_name_conflict"]}},
        severity="BLOCK"
    )
    rule_set = RuleSet(tenant_id="tenant_A", rules=(rule,))
    evaluator = RuleEvaluator(rule_set)
    
    # Mock some context
    context = {"vendor_name_conflict": True, "amount_difference": 0.0}
    
    violations = evaluator.evaluate(context)
    
    assert len(violations) == 1
    assert violations[0].rule_id == "R001"
    assert violations[0].severity == "BLOCK"

def test_rule_evaluator_no_violation():
    rule = Rule(
        rule_id="R001",
        description="Block if vendor conflict",
        condition_ast={"type": "BLOCK", "if": {"type": "AND", "conditions": ["vendor_name_conflict"]}},
        severity="BLOCK"
    )
    rule_set = RuleSet(tenant_id="tenant_A", rules=(rule,))
    evaluator = RuleEvaluator(rule_set)
    
    # Mock some context
    context = {"vendor_name_conflict": False, "amount_difference": 0.0}
    
    violations = evaluator.evaluate(context)
    
    assert len(violations) == 0
