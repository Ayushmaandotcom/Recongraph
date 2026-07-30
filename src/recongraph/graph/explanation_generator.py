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
from recongraph.graph.explanation_templates import ExplanationTemplateRegistry

class ExplanationGenerator:
    """
    Deterministically generates the multi-layer explanation artifact for a given decision.
    """
    def __init__(
        self, 
        trace: DecisionTrace, 
        evidence_graph: EvidenceGraph, 
        fusion_result: FusionResult, 
        decision: ReconciliationDecision,
        template_registry: ExplanationTemplateRegistry | None = None
    ):
        self.trace = trace
        self.evidence_graph = evidence_graph
        self.fusion_result = fusion_result
        self.decision = decision
        self.template_registry = template_registry or ExplanationTemplateRegistry()
        
    def generate(self) -> ExplanationArtifact:
        # Layer 1: Executive Summary
        action = self.decision.action.value
        
        executive_summary = {
            "decision": action,
            "supporting_facts": len(self.fusion_result.independent_support) + len(self.fusion_result.derived_support),
            "contradictions": len(self.fusion_result.contradictions),
            "coverage": f"{self.fusion_result.coverage * 100:.1f}%"
        }
        executive_summary["human_readable"] = self.template_registry.render(
            f"EXECUTIVE_{action}", 
            executive_summary, 
            default="Decision is {decision} with {coverage} coverage and {contradictions} contradictions."
        )
        
        # Layer 2: Domain Summaries
        domain_summaries = {}
        for node_id, node in self.evidence_graph.nodes.items():
            assertion = node.assertion
            domain_summaries[node.domain] = {
                "score": assertion.magnitude,
                "interpretation": repr(assertion.proposition.claim.claim_id.value),
                "violations": sorted(list(frozenset(["CONFLICT"]) if assertion.polarity.name == "CONFLICT" else frozenset()))
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
        trace_vars = {
            "node_id": f"TRACE_{trace_id[:8]}",
            "engine_version": self.trace.engine_version,
            "config_hash": self.trace.config_hash
        }
        trace_node = TraceExplanation(
            node_id=trace_vars["node_id"],
            identity_hash=trace_id,
            dependencies=(),
            engine_version=trace_vars["engine_version"],
            config_hash=trace_vars["config_hash"],
            human_readable=self.template_registry.render("TRACE_NODE", trace_vars, "Trace executed on engine {engine_version} with config {config_hash}.")
        )
        audit_nodes[trace_node.node_id] = trace_node
        
        # 2. Decision Node
        decision_vars = {
            "action": self.decision.action.value,
            "rationale": "Deterministic evaluation of Fusion Result",
            "coverage": self.fusion_result.coverage
        }
        decision_node = DecisionExplanation(
            node_id="DECISION_NODE",
            identity_hash=hashlib.sha256(f"{action}_{self.fusion_result.coverage}".encode()).hexdigest(),
            dependencies=(trace_node.node_id, "FUSION_NODE"),
            action=self.decision.action,
            rationale=str(decision_vars["rationale"]),
            coverage=float(decision_vars["coverage"]),
            human_readable=self.template_registry.render("DECISION_NODE", decision_vars, "Decision: {action}. Rationale: {rationale}.")
        )
        audit_nodes[decision_node.node_id] = decision_node
        
        # 3. Fusion Node
        fusion_vars: dict[str, Any] = {
            "independent_support": len(self.fusion_result.independent_support),
            "derived_support": len(self.fusion_result.derived_support),
            "contradictions": len(self.fusion_result.contradictions),
            "missing_domains": tuple(sorted(self.fusion_result.missingness.keys()))
        }
        fusion_node = FusionExplanation(
            node_id="FUSION_NODE",
            identity_hash=hashlib.sha256(f"{len(self.fusion_result.independent_support)}_{len(self.fusion_result.contradictions)}".encode()).hexdigest(),
            dependencies=tuple(f"PROPAGATION_{n}" for n in self.fusion_result.propagation_status.keys()),
            independent_support=int(fusion_vars["independent_support"]),
            derived_support=int(fusion_vars["derived_support"]),
            contradictions=int(fusion_vars["contradictions"]),
            missing_domains=tuple(fusion_vars["missing_domains"]),
            human_readable=self.template_registry.render("FUSION_NODE", fusion_vars, "Fusion resulted in {independent_support} independent facts, {derived_support} derived, and {contradictions} contradictions.")
        )
        audit_nodes[fusion_node.node_id] = fusion_node
        
        # 4. Propagation and Contribution Nodes
        for node_id, status in self.fusion_result.propagation_status.items():
            prop_node_id = f"PROPAGATION_{node_id}"
            contrib_node_id = f"CONTRIBUTION_{node_id}"
            
            prop_vars: dict[str, Any] = {
                "status": status.value,
                "node_id": node_id
            }
            p_node = PropagationExplanation(
                node_id=prop_node_id,
                identity_hash=hashlib.sha256(f"{node_id}_{status.value}".encode()).hexdigest(),
                dependencies=(contrib_node_id,),
                status=str(prop_vars["status"]),
                derived_from=(), # Can be enhanced by inspecting SemanticPropagator results
                human_readable=self.template_registry.render(f"PROPAGATION_{status.name}", prop_vars, "Propagation status for {node_id} is {status}.")
            )
            audit_nodes[prop_node_id] = p_node
            
            orig_node = self.evidence_graph.nodes[node_id]
            contrib_vars: dict[str, Any] = {
                "provider_name": orig_node.domain,
                "score": orig_node.assertion.magnitude,
                "interpretation": repr(orig_node.assertion.proposition.claim.claim_id.value),
                "violations": list(["CONFLICT"]) if orig_node.assertion.polarity.name == "CONFLICT" else list()
            }
            c_node = ContributionExplanation(
                node_id=contrib_node_id,
                identity_hash=orig_node.node_id, # Reuses the semantic hash from the FusionNode
                dependencies=(), # Would point to Projection/Interpretation nodes in a fully fleshed out graph
                provider_name=str(contrib_vars["provider_name"]),
                score=float(contrib_vars["score"]) if contrib_vars["score"] is not None else None,
                interpretation_repr=str(contrib_vars["interpretation"]),
                violations=frozenset(contrib_vars["violations"]),
                human_readable=self.template_registry.render(f"CONTRIBUTION_{orig_node.domain}", contrib_vars, "Provider {provider_name} contributed evidence for {interpretation} with score {score}.")
            )
            audit_nodes[contrib_node_id] = c_node

        return ExplanationArtifact(
            trace_id=trace_id,
            executive_summary=executive_summary,
            domain_summaries=domain_summaries,
            technical_details=technical_details,
            audit_nodes=audit_nodes
        )
