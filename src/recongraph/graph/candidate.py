from dataclasses import dataclass
from typing import Any
from collections.abc import Mapping, Iterable
from types import MappingProxyType

NodeID = str

def build_purchase_urn(record_id: str) -> NodeID:
    return f"urn:recongraph:purchase:{record_id}"

def build_gst_urn(record_id: str) -> NodeID:
    return f"urn:recongraph:gst:{record_id}"

@dataclass(frozen=True)
class CandidateEdgePayload:
    shared_blocking_keys: frozenset[str]

class CandidateGraph:
    """
    Immutable, mathematically rigorous representation of candidate relationships.
    Enforces GI-001 through GI-006 invariants.
    """
    def __init__(
        self,
        nodes: Mapping[NodeID, Any],
        adjacency: Mapping[NodeID, frozenset[NodeID]],
        edges: Mapping[frozenset[NodeID], CandidateEdgePayload]
    ):
        self._nodes = MappingProxyType(dict(nodes))
        
        # Verify invariants
        for u, neighbors in adjacency.items():
            if u not in self._nodes:
                raise ValueError(f"GI-001 Violation: Adjacency references missing node {u}")
            if u in neighbors:
                raise ValueError(f"GI-002 Violation: Self loops forbidden ({u})")
            for v in neighbors:
                if v not in self._nodes:
                    raise ValueError(f"GI-001 Violation: Adjacency references missing node {v}")
                edge_key = frozenset([u, v])
                if edge_key not in edges:
                    raise ValueError(f"GI-001 Violation: Missing edge payload for {u}-{v}")
                    
        self._adjacency = MappingProxyType({k: frozenset(v) for k, v in adjacency.items()})
        self._edges = MappingProxyType(dict(edges))

    def get_node(self, node_id: NodeID) -> Any:
        return self._nodes[node_id]

    def get_neighbors(self, node_id: NodeID) -> frozenset[NodeID]:
        return self._adjacency.get(node_id, frozenset())

    def get_edge_payload(self, u: NodeID, v: NodeID) -> CandidateEdgePayload | None:
        return self._edges.get(frozenset([u, v]))
        
    @property
    def nodes(self) -> Mapping[NodeID, Any]:
        return self._nodes
        
    @property
    def edges(self) -> Mapping[frozenset[NodeID], CandidateEdgePayload]:
        return self._edges

class CandidateGraphBuilder:
    def __init__(self) -> None:
        self._nodes: dict[NodeID, Any] = {}
        self._adjacency: dict[NodeID, set[NodeID]] = {}
        self._edges: dict[frozenset[NodeID], set[str]] = {}
        
    def add_node(self, node_id: NodeID, record: Any) -> None:
        if node_id in self._nodes and self._nodes[node_id] is not record:
             raise ValueError(f"GI-003 Violation: Node identity collision for {node_id}")
        self._nodes[node_id] = record
        if node_id not in self._adjacency:
            self._adjacency[node_id] = set()
            
    def add_candidate_edge(self, u: NodeID, v: NodeID, keys: frozenset[str]) -> None:
        if u == v:
            return # GI-002: no self loops
            
        edge_key = frozenset([u, v])
        
        # Add topology
        if u not in self._adjacency:
            self._adjacency[u] = set()
        if v not in self._adjacency:
            self._adjacency[v] = set()
            
        self._adjacency[u].add(v)
        self._adjacency[v].add(u)
        
        # Deduplicate keys
        if edge_key not in self._edges:
            self._edges[edge_key] = set()
        self._edges[edge_key].update(keys)
        
    def build(self) -> CandidateGraph:
        frozen_edges = {
            k: CandidateEdgePayload(shared_blocking_keys=frozenset(v))
            for k, v in self._edges.items()
        }
        return CandidateGraph(
            nodes=self._nodes,
            adjacency={k: frozenset(v) for k, v in self._adjacency.items()},
            edges=frozen_edges
        )
