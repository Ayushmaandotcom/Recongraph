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
def mock_fusion_result():
    return FusionResult(
        independent_support=frozenset(["TAX_NODE", "FINANCIAL_NODE"]),
        derived_support=frozenset(["VENDOR_NODE"]),
        contradictions=frozenset([]),
        dependency_groups=(),
        missingness={"TEMPORAL_NODE": "missing_record"},
        propagation_status={
            "TAX_NODE": PropagationStatus.SUPPORTED,
            "FINANCIAL_NODE": PropagationStatus.SUPPORTED,
            "VENDOR_NODE": PropagationStatus.SUPPORTED
        },
        coverage=0.9
    )

@pytest.fixture
def mock_evidence_graph():
    graph = EvidenceGraph()
    
    contrib1 = EvidenceContributionV2(provider_name="TAX", score=1.0)
    node1 = FusionNode(node_id="TAX_NODE", contribution=contrib1)
    
    contrib2 = EvidenceContributionV2(provider_name="FINANCIAL", score=1.0)
    node2 = FusionNode(node_id="FINANCIAL_NODE", contribution=contrib2)
    
    contrib3 = EvidenceContributionV2(provider_name="VENDOR", score=0.9)
    node3 = FusionNode(node_id="VENDOR_NODE", contribution=contrib3)
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    return graph

def test_determinism_audit(mock_trace, mock_evidence_graph, mock_fusion_result, mock_decision):
    generator = ExplanationGenerator(mock_trace, mock_evidence_graph, mock_fusion_result, mock_decision)
    artifact1 = generator.generate()
    artifact2 = generator.generate()
    
    assert artifact1.executive_summary == artifact2.executive_summary
    assert artifact1.audit_nodes.keys() == artifact2.audit_nodes.keys()

def test_completeness_audit(mock_trace, mock_evidence_graph, mock_fusion_result, mock_decision):
    generator = ExplanationGenerator(mock_trace, mock_evidence_graph, mock_fusion_result, mock_decision)
    artifact = generator.generate()
    
    # Verify no orphan nodes: every node in the evidence graph should have a corresponding contribution node
    for node_id in mock_evidence_graph.nodes:
        assert f"CONTRIBUTION_{node_id}" in artifact.audit_nodes

def test_mermaid_export(mock_trace, mock_evidence_graph, mock_fusion_result, mock_decision):
    generator = ExplanationGenerator(mock_trace, mock_evidence_graph, mock_fusion_result, mock_decision)
    artifact = generator.generate()
    
    exporter = MermaidExporter()
    mermaid_output = exporter.export(artifact)
    
    assert "graph TD" in mermaid_output
    assert "subgraph Evidence Contributions" in mermaid_output
    assert "subgraph Semantic Propagation" in mermaid_output
    assert "FUSION_NODE" in mermaid_output
    assert "DECISION_NODE" in mermaid_output
