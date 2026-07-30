import pytest
from recongraph.graph.fusion import FusionNode, EvidenceGraph, DependencyEdge, ContradictionEdge
from recongraph.contrib.kernel.assertions import EvidenceAssertion, AssertionPolarity, EvidenceAncestryRef
from recongraph.contrib.kernel.scopes import Proposition, ScopeKind, SubjectRef
from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
from recongraph.contrib.kernel.claims import ClaimDescriptor, ClaimId, ClaimSemanticVersion, ClaimSymmetry

def make_dummy_assertion(basis_name: str, magnitude: float = 1.0, polarity: AssertionPolarity = AssertionPolarity.SUPPORT) -> EvidenceAssertion:
    mock_ancestry = EvidenceAncestryRef(
        identity=KernelIdentityRef(
            domain=IdentityDomainId("recongraph.observation_occurrence"),
            schema=IdentitySchemaId("recongraph.observation_occurrence.v1"),
            digest=IdentityDigest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
        )
    )
    dummy_claim = ClaimDescriptor(
        claim_id=ClaimId("dummy.claim"),
        semantic_version=ClaimSemanticVersion(1),
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
    )
    return EvidenceAssertion(
        proposition=Proposition.create(claim=dummy_claim, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:left")], right=[SubjectRef("urn:right")]),
        polarity=polarity,
        magnitude=magnitude,
        authority=AuthorityDescriptor(basis=AuthorityBasisId(basis_name)),
        ancestry=mock_ancestry
    )

def test_fusion_node_determinism():
    assert1 = make_dummy_assertion("TAX_IDENTITY")
    assert2 = make_dummy_assertion("TAX_IDENTITY")
    
    node1 = FusionNode.from_assertion(assert1)
    node2 = FusionNode.from_assertion(assert2)
    
    assert node1.node_id == node2.node_id
    
def test_fusion_node_distinct():
    assert1 = make_dummy_assertion("TAX_IDENTITY")
    assert2 = make_dummy_assertion("VENDOR_IDENTITY")
    
    node1 = FusionNode.from_assertion(assert1)
    node2 = FusionNode.from_assertion(assert2)
    
    assert node1.node_id != node2.node_id

def test_evidence_graph_permutation_invariance():
    assert_tax = make_dummy_assertion("TAX")
    assert_ven = make_dummy_assertion("VENDOR", magnitude=0.9)
    assert_fin = make_dummy_assertion("FINANCIAL")
    
    node_tax = FusionNode.from_assertion(assert_tax)
    node_ven = FusionNode.from_assertion(assert_ven)
    node_fin = FusionNode.from_assertion(assert_fin)
    
    dep_edge = DependencyEdge(_source_id=node_tax.node_id, _target_id=node_ven.node_id)
    con_edge = ContradictionEdge(node_a=node_tax.node_id, node_b=node_fin.node_id)
    
    graph_a = EvidenceGraph()
    graph_a.add_node(node_tax)
    graph_a.add_node(node_ven)
    graph_a.add_node(node_fin)
    graph_a.add_edge(dep_edge)
    graph_a.add_edge(con_edge)
    
    graph_b = EvidenceGraph()
    graph_b.add_node(node_fin)
    graph_b.add_node(node_tax)
    graph_b.add_node(node_ven)
    graph_b.add_edge(con_edge)
    graph_b.add_edge(dep_edge)
    
    assert graph_a.identity == graph_b.identity
    assert len(graph_a.nodes) == 3
    assert len(graph_a.edges) == 2

def test_evidence_graph_missing_node_edge():
    node = FusionNode.from_assertion(make_dummy_assertion("TAX"))
    graph = EvidenceGraph()
    
    with pytest.raises(ValueError, match="Cannot add edge"):
        graph.add_edge(DependencyEdge(_source_id=node.node_id, _target_id="fake_id"))
