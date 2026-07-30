from typing import Any
from recongraph.graph.fusion_explainability import ExplanationArtifact

class MermaidExporter:
    def export(self, artifact: ExplanationArtifact) -> str:
        lines = ["graph TD"]
        lines.append("classDef support fill:#e6fffa,stroke:#38b2ac,stroke-width:2px")
        
        lines.append("subgraph Semantic Propagation")
        for node_id in artifact.audit_nodes:
            if node_id.startswith("PROPAGATION_"):
                lines.append(f"  {node_id}[Propagation]")
        lines.append("end")
        
        lines.append("subgraph Evidence Contributions")
        for node_id in artifact.audit_nodes:
            if node_id.startswith("CONTRIBUTION_"):
                lines.append(f"  {node_id}[Contribution]")
        lines.append("end")
        
        lines.append("FUSION_NODE[Fusion]")
        lines.append("DECISION_NODE[Decision]")
        
        return "\n".join(lines)
