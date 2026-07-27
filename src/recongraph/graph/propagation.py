from dataclasses import dataclass
from typing import Mapping, Set, List
from enum import Enum
from recongraph.graph.fusion import EvidenceGraph, FusionNode, DependencyEdge, ContradictionEdge, CorroborationEdge

class TopologicalCycleError(ValueError):
    """Raised when a directed dependency cycle is detected."""
    pass

class PropagationStatus(Enum):
    UNAFFECTED = "UNAFFECTED"
    SUPPORTED = "SUPPORTED"
    QUESTIONED = "QUESTIONED"
    CONTRADICTED = "CONTRADICTED"
    INVALIDATED = "INVALIDATED"

@dataclass
class PropagatedNode:
    """
    A FusionNode enriched with semantic markers from propagation.
    """
    original_node: FusionNode
    status: PropagationStatus = PropagationStatus.UNAFFECTED
    derived_support_sources: frozenset[str] = frozenset()
    corroborators: frozenset[str] = frozenset()
    
    @property
    def node_id(self) -> str:
        return self.original_node.node_id
        
    @property
    def domain(self) -> str:
        return self.original_node.domain

class SemanticPropagator:
    """
    Evaluates topological constraints (dependencies, contradictions) across the EvidenceGraph
    without computing final fused scores.
    """
    @staticmethod
    def propagate(graph: EvidenceGraph) -> Mapping[str, PropagatedNode]:
        propagated = {}
        for node_id, node in graph.nodes.items():
            status = PropagationStatus.UNAFFECTED
            if node.contribution.violations:
                status = PropagationStatus.CONTRADICTED
            elif node.contribution.score is None or node.contribution.score <= 0.0:
                status = PropagationStatus.INVALIDATED
                
            propagated[node_id] = PropagatedNode(node, status=status)
        
        # 1. Detect Cycles and Topological Sort (DependencyEdges only)
        # We perform a DFS to detect back-edges.
        visited: Set[str] = set()
        recursion_stack: Set[str] = set()
        
        # Build adjacency lists for dependencies
        downstream: Mapping[str, List[str]] = {node_id: [] for node_id in graph.nodes}
        upstream: Mapping[str, List[str]] = {node_id: [] for node_id in graph.nodes}
        contradictions: Mapping[str, List[str]] = {node_id: [] for node_id in graph.nodes}
        corroborations: Mapping[str, List[str]] = {node_id: [] for node_id in graph.nodes}
        
        for edge in graph.edges.values():
            if isinstance(edge, DependencyEdge):
                downstream[edge.source_id].append(edge.target_id)
                upstream[edge.target_id].append(edge.source_id)
            elif isinstance(edge, ContradictionEdge):
                contradictions[edge.source_id].append(edge.target_id)
                contradictions[edge.target_id].append(edge.source_id)
            elif isinstance(edge, CorroborationEdge):
                corroborations[edge.source_id].append(edge.target_id)
                corroborations[edge.target_id].append(edge.source_id)
                
        def dfs_detect_cycle(node_id: str) -> None:
            visited.add(node_id)
            recursion_stack.add(node_id)
            
            for neighbor in downstream[node_id]:
                if neighbor not in visited:
                    dfs_detect_cycle(neighbor)
                elif neighbor in recursion_stack:
                    raise TopologicalCycleError(f"Directed dependency cycle detected involving {node_id} and {neighbor}")
                    
            recursion_stack.remove(node_id)
            
        for node_id in graph.nodes:
            if node_id not in visited:
                dfs_detect_cycle(node_id)
                
        # 2. Propagate Corroboration (Transitive within same domain, intransitive across)
        for node_id in graph.nodes:
            propagated[node_id].corroborators = frozenset(corroborations[node_id])
            
        # 3. Propagate Derived Support (Downstream along DependencyEdges)
        memoized_ancestors: dict[str, set[str]] = {}
        def get_all_ancestors(node_id: str) -> set[str]:
            if node_id in memoized_ancestors:
                return memoized_ancestors[node_id]
            ancestors = set(upstream[node_id])
            for parent in upstream[node_id]:
                ancestors.update(get_all_ancestors(parent))
            memoized_ancestors[node_id] = ancestors
            return ancestors
            
        for node_id in graph.nodes:
            ancestors = get_all_ancestors(node_id)
            propagated[node_id].derived_support_sources = frozenset(ancestors)
            if ancestors and propagated[node_id].status == PropagationStatus.UNAFFECTED:
                propagated[node_id].status = PropagationStatus.SUPPORTED
                
        # 4. Propagate Contradictions
        # Direct contradictions -> CONTRADICTED
        # Upstream of a contradicted node -> QUESTIONED
        
        contradicted_nodes = set()
        for node_id, contras in contradictions.items():
            if contras:
                contradicted_nodes.add(node_id)
                propagated[node_id].status = PropagationStatus.CONTRADICTED
                
        questioned_nodes = set()
        def propagate_questioned_upstream(node_id: str) -> None:
            for parent in upstream[node_id]:
                if parent not in questioned_nodes and parent not in contradicted_nodes:
                    questioned_nodes.add(parent)
                    propagate_questioned_upstream(parent)
                    
        for c_node in contradicted_nodes:
            propagate_questioned_upstream(c_node)
            
        for q_node in questioned_nodes:
            # Only downgrade to QUESTIONED if it wasn't strictly CONTRADICTED or INVALIDATED
            if propagated[q_node].status not in (PropagationStatus.CONTRADICTED, PropagationStatus.INVALIDATED):
                propagated[q_node].status = PropagationStatus.QUESTIONED
            
        return propagated
