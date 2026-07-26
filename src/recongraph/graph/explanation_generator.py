import hashlib
from typing import Mapping, Any
from recongraph.graph.decision import ReconciliationDecision
from recongraph.graph.trace import DecisionTrace
from recongraph.graph.fusion_result import FusionResult
from recongraph.graph.fusion import EvidenceGraph
from recongraph.graph.fusion_explainability import (
    ExplanationArtifact,
    DecisionExplanation,
    FusionExplanation,
    PropagationExplanation,
    ContributionExplanation,
    TraceExplanation,
    ExplanationNode
)
from recongraph.plugins.provider_v2 import EvidenceContributionV2

class ExplanationGenerator:
    """
    Deterministically generates the multi-layer explanation artifact for a given decision.
    """
    def __init__(self, trace: DecisionTrace, evidence_graph: EvidenceGraph, fusion_result: FusionResult, decision: ReconciliationDecision):
        self.trace = trace
        self.evidence_graph = evidence_graph
        self.fusion_result = fusion_result
        self.decision = decision
        
    def generate(self) -> ExplanationArtifact:
        # Layer 1: Executive Summary
        action = self.decision.action.value
        
        executive_summary = {
            "decision": action,
            "supporting_facts": len(self.fusion_result.independent_support) + len(self.fusion_result.derived_support),
            "contradictions": len(self.fusion_result.contradictions),
            "coverage": f"{self.fusion_result.coverage * 100:.1f}%"
        }
        
        # Layer 2: Domain Summaries
        domain_summaries = {}
        for node_id, node in self.evidence_graph.nodes.items():
            contrib = node.contribution
            domain_summaries[node.domain] = {
                "score": contrib.score,
                "interpretation": repr(contrib.interpretation) if contrib.interpretation else "None",
                "violations": sorted(list(contrib.violations))
            }
            
        # Layer 3: Technical Details
        technical_details = {
            "independent_support": sorted(list(self.fusion_result.independent_support)),
            "derived_support": sorted(list(self.fusion_result.derived_support)),
            "contradicted": sorted(list(self.fusion_result.contradictions)),
            "missingness": dict(self.fusion_result.missingness),
            "dependency_groups": [sorted(list(g)) for g in self.fusion_result.dependency_groups]
        }
        
        # Layer 4: Audit Nodes
        audit_nodes: dict[str, ExplanationNode] = {}
        
        # 1. Trace Node
        trace_id = self.trace.trace_id
        trace_node = TraceExplanation(
            node_id=f"TRACE_{trace_id[:8]}",
            identity_hash=trace_id,
            dependencies=(),
            engine_version=self.trace.engine_version,
            config_hash=self.trace.config_hash
        )
        audit_nodes[trace_node.node_id] = trace_node
        
        # 2. Decision Node
        decision_node = DecisionExplanation(
            node_id="DECISION_NODE",
            identity_hash=hashlib.sha256(f"{action}_{self.fusion_result.coverage}".encode()).hexdigest(),
            dependencies=(trace_node.node_id, "FUSION_NODE"),
            action=action,
            rationale="Deterministic evaluation of Fusion Result",
            coverage=self.fusion_result.coverage
        )
        audit_nodes[decision_node.node_id] = decision_node
        
        # 3. Fusion Node
        fusion_node = FusionExplanation(
            node_id="FUSION_NODE",
            identity_hash=hashlib.sha256(f"{len(self.fusion_result.independent_support)}_{len(self.fusion_result.contradictions)}".encode()).hexdigest(),
            dependencies=tuple(f"PROPAGATION_{n}" for n in self.fusion_result.propagation_status.keys()),
            independent_support=len(self.fusion_result.independent_support),
            derived_support=len(self.fusion_result.derived_support),
            contradictions=len(self.fusion_result.contradictions),
            missing_domains=tuple(sorted(self.fusion_result.missingness.keys()))
        )
        audit_nodes[fusion_node.node_id] = fusion_node
        
        # 4. Propagation and Contribution Nodes
        for node_id, status in self.fusion_result.propagation_status.items():
            prop_node_id = f"PROPAGATION_{node_id}"
            contrib_node_id = f"CONTRIBUTION_{node_id}"
            
            p_node = PropagationExplanation(
                node_id=prop_node_id,
                identity_hash=hashlib.sha256(f"{node_id}_{status.value}".encode()).hexdigest(),
                dependencies=(contrib_node_id,),
                status=status.value,
                derived_from=() # Can be enhanced by inspecting SemanticPropagator results
            )
            audit_nodes[prop_node_id] = p_node
            
            orig_node = self.evidence_graph.nodes[node_id]
            c_node = ContributionExplanation(
                node_id=contrib_node_id,
                identity_hash=orig_node.node_id, # Reuses the semantic hash from the FusionNode
                dependencies=(), # Would point to Projection/Interpretation nodes in a fully fleshed out graph
                provider_name=orig_node.domain,
                score=orig_node.contribution.score,
                interpretation_repr=repr(orig_node.contribution.interpretation) if orig_node.contribution.interpretation else None,
                violations=orig_node.contribution.violations
            )
            audit_nodes[contrib_node_id] = c_node

        return ExplanationArtifact(
            trace_id=trace_id,
            executive_summary=executive_summary,
            domain_summaries=domain_summaries,
            technical_details=technical_details,
            audit_nodes=audit_nodes
        )
