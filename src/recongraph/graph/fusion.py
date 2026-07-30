from dataclasses import dataclass, field
import hashlib
from typing import Mapping, Sequence, TypeVar, Generic, Iterable, Any
from recongraph.contrib.kernel.assertions import EvidenceAssertion

@dataclass(frozen=True)
class FusionNode:
    """
    A vertex in the EvidenceGraph representing a single typed evidence assertion.
    """
    node_id: str
    assertion: EvidenceAssertion
    
    @property
    def domain(self) -> str:
        return str(self.assertion.authority.basis.value)
        
    @property
    def version(self) -> str:
        return str(self.assertion.proposition.claim.semantic_version.value)
        
    @property
    def provenance(self) -> str:
        return str(self.assertion.authority.basis.value)
        
    @property
    def dependencies(self) -> list[str]:
        return []

    def to_dict(self) -> dict[str, Any]:
        import json
        from recongraph.serialization import ReconEncoder
        return {
            "node_id": self.node_id,
            "assertion": json.loads(json.dumps(self.assertion, cls=ReconEncoder))
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'FusionNode':
        raise NotImplementedError("from_dict is deprecated for FusionNode until ReconDecoder is implemented")

    @classmethod
    def from_assertion(cls, assertion: EvidenceAssertion) -> 'FusionNode':
        h = hashlib.sha256()
        h.update(str(assertion.authority.basis.value).encode('utf-8'))
        h.update(str(assertion.proposition.claim.claim_id.value).encode('utf-8'))
        h.update(str(assertion.polarity.value).encode('utf-8'))
        h.update(str(round(assertion.magnitude, 6)).encode('utf-8'))
            
        node_id = f"fn_{h.hexdigest()[:16]}"
        return cls(node_id=node_id, assertion=assertion)

class EvidenceEdge:
    """Base class for topological links between FusionNodes."""
    @property
    def source_id(self) -> str:
        raise NotImplementedError
        
    @property
    def target_id(self) -> str:
        raise NotImplementedError
        
    @property
    def canonical_identity(self) -> str:
        raise NotImplementedError
        
    @property
    def is_directed(self) -> bool:
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

@dataclass(frozen=True)
class DependencyEdge(EvidenceEdge):
    """
    A directed edge indicating the target is derived from the source.
    (e.g., Vendor derived from Tax PAN)
    """
    _source_id: str
    _target_id: str
    
    @property
    def source_id(self) -> str:
        return self._source_id
        
    @property
    def target_id(self) -> str:
        return self._target_id
    
    @property
    def canonical_identity(self) -> str:
        return f"dep:{self.source_id}->{self.target_id}"

    @property
    def is_directed(self) -> bool:
        return True

    def to_dict(self) -> dict[str, Any]:
        return {"type": "DependencyEdge", "source_id": self.source_id, "target_id": self.target_id}

@dataclass(frozen=True)
class ContradictionEdge(EvidenceEdge):
    """
    An undirected edge indicating mutual exclusion.
    """
    node_a: str
    node_b: str
    
    @property
    def source_id(self) -> str:
        return self.node_a
        
    @property
    def target_id(self) -> str:
        return self.node_b
        
    @property
    def canonical_identity(self) -> str:
        a, b = sorted([self.node_a, self.node_b])
        return f"contra:{a}--{b}"

    @property
    def is_directed(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        return {"type": "ContradictionEdge", "node_a": self.node_a, "node_b": self.node_b}

@dataclass(frozen=True)
class CorroborationEdge(EvidenceEdge):
    """
    An undirected edge indicating independent support.
    """
    node_a: str
    node_b: str
    
    @property
    def source_id(self) -> str:
        return self.node_a
        
    @property
    def target_id(self) -> str:
        return self.node_b
        
    @property
    def canonical_identity(self) -> str:
        a, b = sorted([self.node_a, self.node_b])
        return f"corr:{a}--{b}"

    @property
    def is_directed(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        return {"type": "CorroborationEdge", "node_a": self.node_a, "node_b": self.node_b}

def edge_from_dict(data: dict[str, Any]) -> EvidenceEdge:
    edge_type = data["type"]
    if edge_type == "DependencyEdge":
        return DependencyEdge(_source_id=data["source_id"], _target_id=data["target_id"])
    elif edge_type == "ContradictionEdge":
        return ContradictionEdge(node_a=data["node_a"], node_b=data["node_b"])
    elif edge_type == "CorroborationEdge":
        return CorroborationEdge(node_a=data["node_a"], node_b=data["node_b"])
    raise ValueError(f"Unknown edge type {edge_type}")

class EvidenceGraph:
    """
    A Topological DAG containing FusionNodes and EvidenceEdges.
    """
    def __init__(self) -> None:
        self._nodes: dict[str, FusionNode] = {}
        self._edges: dict[str, EvidenceEdge] = {}
        
    def add_node(self, node: FusionNode) -> None:
        if node.node_id not in self._nodes:
            self._nodes[node.node_id] = node
            
    def add_edge(self, edge: EvidenceEdge) -> None:
        if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
            raise ValueError(f"Cannot add edge {edge.canonical_identity}; missing nodes.")
            
        edge_id = edge.canonical_identity
        if edge_id not in self._edges:
            self._edges[edge_id] = edge
            
    @property
    def nodes(self) -> Mapping[str, FusionNode]:
        return self._nodes
        
    @property
    def edges(self) -> Mapping[str, EvidenceEdge]:
        return self._edges
        
    @property
    def identity(self) -> str:
        """
        Computes a deterministic hash of the entire graph, proving permutation invariance.
        """
        h = hashlib.sha256()
        for node_id in sorted(self._nodes.keys()):
            h.update(node_id.encode('utf-8'))
            
        for edge_id in sorted(self._edges.keys()):
            h.update(edge_id.encode('utf-8'))
            
        return f"eg_{h.hexdigest()}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges.values()]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'EvidenceGraph':
        graph = cls()
        for node_data in data["nodes"]:
            graph.add_node(FusionNode.from_dict(node_data))
        for edge_data in data["edges"]:
            graph.add_edge(edge_from_dict(edge_data))
        return graph
