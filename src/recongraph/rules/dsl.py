import re
from typing import Any, Mapping
from recongraph.rules.models import Rule

def parse_rule(rule_id: str, description: str, rule_string: str) -> Rule:
    """Parses a simple DSL rule string into a Rule object."""
    rule_string = rule_string.strip()
    
    if rule_string.startswith("REQUIRE"):
        # e.g., REQUIRE tax_identity_match WHEN amount_difference > 0
        match = re.match(r"REQUIRE\s+(\w+)\s+WHEN\s+(\w+)\s+([><=]+)\s+(.+)", rule_string)
        if match:
            target, left, op, right = match.groups()
            
            # try to parse right as float or int if possible
            try:
                if "." in right:
                    right = float(right)
                else:
                    right = int(right)
            except ValueError:
                pass
                
            ast = {
                "type": "REQUIRE",
                "target": target,
                "when": {
                    "left": left,
                    "operator": op,
                    "right": right
                }
            }
            return Rule(rule_id=rule_id, description=description, condition_ast=ast, severity="REQUIRE")
            
    elif rule_string.startswith("BLOCK IF"):
        # e.g., BLOCK IF vendor_name_conflict AND missing_reference
        match = re.match(r"BLOCK IF\s+(.+)", rule_string)
        if match:
            condition_str = match.group(1)
            if " AND " in condition_str:
                conditions = condition_str.split(" AND ")
                ast = {
                    "type": "BLOCK",
                    "if": {
                        "type": "AND",
                        "conditions": [c.strip() for c in conditions]
                    }
                }
                return Rule(rule_id=rule_id, description=description, condition_ast=ast, severity="BLOCK")
                
    raise ValueError(f"Failed to parse rule string: {rule_string}")
