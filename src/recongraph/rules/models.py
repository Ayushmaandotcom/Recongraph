from dataclasses import dataclass
from typing import Any, Mapping

@dataclass(frozen=True, slots=True)
class RuleViolation:
    rule_id: str
    description: str
    severity: str  # 'BLOCK', 'REQUIRE'

@dataclass(frozen=True, slots=True)
class Rule:
    rule_id: str
    description: str
    condition_ast: Mapping[str, Any]
    severity: str

@dataclass(frozen=True, slots=True)
class RuleSet:
    tenant_id: str
    rules: tuple[Rule, ...]
