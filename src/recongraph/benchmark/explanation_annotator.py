import json
from pathlib import Path
from typing import Iterator

from recongraph.graph.fusion_explainability import ExplanationArtifact
from recongraph.graph.explanation_templates import ExplanationTemplateRegistry

class ExplanationAnnotator:
    """
    Offline tool for managing and comparing ExplanationArtifacts against human-curated explanations.
    """
    def __init__(self, template_registry: ExplanationTemplateRegistry):
        self.template_registry = template_registry
        
    def generate_diff(self, artifact: ExplanationArtifact, annotated_layer1: str) -> dict[str, str]:
        """
        Compare the generated Executive Summary human-readable string with the 
        annotated (ideal) string to help reviewers update templates.
        """
        action = artifact.executive_summary.get("decision", "UNKNOWN")
        template_key = f"EXECUTIVE_{action}"
        
        current_template = self.template_registry.get_template(
            template_key, 
            default="Decision is {decision} with {coverage} coverage and {contradictions} contradictions."
        )
        
        return {
            "template_key": template_key,
            "current_template": current_template,
            "suggested_target": annotated_layer1,
            "variables_available": list(artifact.executive_summary.keys())
        }

    def suggest_template_update(self, diffs: list[dict[str, str]], out_path: Path):
        """
        Takes human feedback diffs and saves a proposed update to the JSON templates.
        """
        updates = dict(self.template_registry._templates)
        for diff in diffs:
            # Here a real system might use an LLM or heuristics to map the annotated
            # string back to a generic format string. We just log the suggestion.
            updates[diff["template_key"]] = diff["suggested_target"]
            
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(updates, f, indent=2)
