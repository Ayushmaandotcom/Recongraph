from typing import Any, Mapping, Sequence
from recongraph.rules.models import RuleSet, RuleViolation

class RuleEvaluator:
    """Evaluates a set of business rules against a reconciliation context."""
    
    def __init__(self, rule_set: RuleSet):
        self.rule_set = rule_set
        
    def evaluate(self, context: Mapping[str, Any]) -> Sequence[RuleViolation]:
        violations = []
        
        for rule in self.rule_set.rules:
            if self._evaluate_condition(rule.condition_ast, context):
                violations.append(
                    RuleViolation(
                        rule_id=rule.rule_id,
                        description=rule.description,
                        severity=rule.severity
                    )
                )
                
        return tuple(violations)
        
    def _evaluate_condition(self, ast: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
        if ast["type"] == "BLOCK":
            return self._evaluate_if(ast["if"], context)
        elif ast["type"] == "REQUIRE":
            # For REQUIRE, the condition failing means a violation occurred.
            # e.g., REQUIRE tax_identity_match WHEN amount_difference > 0
            # Violation happens if WHEN is true but TARGET is false.
            when_true = self._evaluate_when(ast.get("when", {}), context)
            if when_true:
                target_met = context.get(ast["target"], False)
                return not target_met
            return False
            
        return False
        
    def _evaluate_if(self, if_ast: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
        if if_ast["type"] == "AND":
            # True if all conditions are true
            for condition in if_ast["conditions"]:
                if not context.get(condition, False):
                    return False
            return True
        return False

    def _evaluate_when(self, when_ast: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
        if not when_ast:
            return True
            
        left_val = context.get(when_ast["left"])
        right_val = when_ast["right"]
        op = when_ast["operator"]
        
        if left_val is None:
            return False
            
        if op == ">":
            return left_val > right_val
        elif op == "<":
            return left_val < right_val
        elif op == "==":
            return left_val == right_val
        elif op == ">=":
            return left_val >= right_val
        elif op == "<=":
            return left_val <= right_val
            
        return False
