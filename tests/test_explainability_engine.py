import pytest
import hashlib
from datetime import datetime, timezone
from recongraph.graph.fusion_explainability import ExplanationArtifact
from recongraph.graph.explanation_generator import ExplanationGenerator
from recongraph.graph.visualizers import MermaidExporter
from recongraph.graph.trace import DecisionTrace, TraceStage, TraceEvent
from recongraph.graph.decision import ReconciliationDecision, DecisionAction
from recongraph.graph.fusion import EvidenceGraph, FusionNode
from recongraph.graph.fusion_result import FusionResult
from recongraph.graph.propagation import PropagationStatus
from recongraph.plugins.provider_v2 import EvidenceContributionV2

@pytest.fixture
def mock_trace():
    return DecisionTrace(
        trace_id="TRACE_12345",
        engine_version="1.0.0",
        config_hash="CONFIG_HASH",
        events=()
    )

@pytest.fixture
def mock_decision():
    from recongraph.graph.decision import ReconciliationDecision, DecisionAction
    return ReconciliationDecision(
        action=DecisionAction.AUTO_MATCH,
        selected_hypothesis=None,
        competitors=(),
        rationale="Mock rationale"
    )

@pytest.fixture
def mock_graph_and_result():
    from recongraph.contrib.kernel.assertions import EvidenceAssertion, AssertionPolarity, EvidenceAncestryRef
    from recongraph.contrib.kernel.scopes import Proposition, ScopeKind, SubjectRef
    from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
    from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
    from recongraph.contrib.kernel.claims import ClaimDescriptor, ClaimId, ClaimSemanticVersion, ClaimSymmetry
    from recongraph.graph.fusion import DependencyEdge, CorroborationEdge
    
    def make_dummy(name: str, magnitude: float = 1.0, polarity: AssertionPolarity = AssertionPolarity.SUPPORT):
        mock_ancestry = EvidenceAncestryRef(
            identity=KernelIdentityRef(
                domain=IdentityDomainId("recongraph.observation_occurrence"),
                schema=IdentitySchemaId("recongraph.observation_occurrence.v1"),
                digest=IdentityDigest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
            )
        )
        dummy_claim = ClaimDescriptor(claim_id=ClaimId(f"dummy.{name.lower()}"), semantic_version=ClaimSemanticVersion(1), symmetry=ClaimSymmetry.SYMMETRIC, allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR}))
        return EvidenceAssertion(
            proposition=Proposition.create(claim=dummy_claim, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:left")], right=[SubjectRef("urn:right")]),
            polarity=polarity, magnitude=magnitude, authority=AuthorityDescriptor(basis=AuthorityBasisId(name)), ancestry=mock_ancestry
        )

    graph = EvidenceGraph()
    node1 = FusionNode.from_assertion(make_dummy("TAX"))
    node2 = FusionNode.from_assertion(make_dummy("VENDOR", magnitude=0.9))
    node3 = FusionNode.from_assertion(make_dummy("AMOUNT"))
    node4 = FusionNode.from_assertion(make_dummy("TEMPORAL", magnitude=0.8))
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    graph.add_node(node4)
    
    # Simulate some propagation structure
    graph.add_edge(DependencyEdge(_source_id=node1.node_id, _target_id=node2.node_id))
    graph.add_edge(CorroborationEdge(node_a=node2.node_id, node_b=node3.node_id))
    
    fusion_result = FusionResult(
        independent_support=frozenset([node1.node_id, node3.node_id]),
        derived_support=frozenset([node2.node_id]),
        contradictions=frozenset([]),
        dependency_groups=(),
        missingness={node4.node_id: "missing_record"},
        propagation_status={
            node1.node_id: PropagationStatus.SUPPORTED,
            node2.node_id: PropagationStatus.SUPPORTED,
            node3.node_id: PropagationStatus.SUPPORTED,
            node4.node_id: PropagationStatus.UNAFFECTED
        },
        coverage=0.9
    )
    
    return graph, fusion_result

def test_determinism_audit(mock_trace, mock_graph_and_result, mock_decision):
    graph, fusion_result = mock_graph_and_result
    generator = ExplanationGenerator(mock_trace, graph, fusion_result, mock_decision)
    artifact1 = generator.generate()
    artifact2 = generator.generate()
    
    assert artifact1.executive_summary == artifact2.executive_summary
    assert artifact1.audit_nodes.keys() == artifact2.audit_nodes.keys()

def test_completeness_audit(mock_trace, mock_graph_and_result, mock_decision):
    graph, fusion_result = mock_graph_and_result
    generator = ExplanationGenerator(mock_trace, graph, fusion_result, mock_decision)
    artifact = generator.generate()
    
    # Verify all graph nodes are accounted for in audit
    for node_id in graph.nodes.keys():
        assert f"PROPAGATION_{node_id}" in artifact.audit_nodes

def test_mermaid_export(mock_trace, mock_graph_and_result, mock_decision):
    from recongraph.graph.mermaid_exporter import MermaidExporter
    graph, fusion_result = mock_graph_and_result
    generator = ExplanationGenerator(mock_trace, graph, fusion_result, mock_decision)
    artifact = generator.generate()
    
    exporter = MermaidExporter()
    mermaid_str = exporter.export(artifact)
    assert "graph TD" in mermaid_str
    assert "classDef support fill:#e6fffa,stroke:#38b2ac,stroke-width:2px" in mermaid_str
    assert "DECISION_NODE" in mermaid_str
    assert "subgraph Semantic Propagation" in mermaid_str
    assert "FUSION_NODE" in mermaid_str
